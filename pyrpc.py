import socket
import selectors
import types
import os
import sys
import imp
import json

from urllib.parse import splitnport as parse_addr
from threading import Thread

RECV_SIZE = 1024
ENC = "json"

################################################################################

def acceptor(srv):
    def f(sock):
        conn, addr = sock.accept()
        conn.setblocking(False)
        srv.sel.register(conn, selectors.EVENT_READ, srv._handle)
    return f


class GolangStyleImplLoaderMeta(type):
    '''
    Function-loading metaclass inspired by 
    http://stackoverflow.com/questions/9865455/adding-functions-from-other-files-to-a-python-class
    '''
    def __new__(cls, name, bases, dct):
        modules = [imp.load_source(fn, fn) for fn in os.listdir('.') if fn.startswith('rpc_') and fn.endswith('.py')]
        for module in modules:
            for nm in dir(module):
                f = getattr(module, nm)
                if isinstance(f, types.FunctionType):
                    dct[f.__name__] = f
        return super(GolangStyleImplLoaderMeta, cls).__new__(cls, name, bases, dct)

################################################################################

class RpcMessage(dict):

    STATUS_OK = 0
    STATUS_ERR = 1
    STATUS_WARN = 2

    def __init__(self, *args, **kwargs):
        super(RpcMessage, self).__init__(*args, **kwargs)
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def Encode(self, enc):
        if enc == "json":
            return ("%s.%s" % (enc, json.dumps(self))).encode('utf8')
        raise ValueError("Invalid message enc: %s" % enc)

    @staticmethod
    def Decode(msgstr):
        enc, msg = msgstr.decode('utf8').split(".", 1)
        if enc == "json":
            return RpcMessage(**json.loads(msg))
        raise ValueError("Invalid message enc: %s" % enc)

class _RpcServer(object):
    running = False
    enc = "json"
    sel = selectors.DefaultSelector()
    funs = {}
    
    # error check

    def error(self, msg):
        return RpcMessage(ok=False, msg=msg)

    def _checkReady(m):
        def proxy(self, *args):
            if self.running:
                return m(self, *args)
            else:
                raise Exception("RpcModule is not initialized!")
        return proxy

    @_checkReady
    def _send(self, conn, reply):
        conn.sendall(reply.Encode(ENC))

    @_checkReady
    def _handle(self, conn):
        sender = RpcRemote(conn.getpeername())
        data = conn.recv(RECV_SIZE)
        if data:
            try:
                msg = RpcMessage.Decode(data) 
                method = msg["method"]
                if method in self.funs:
                    fun = self.funs[method]
                    val = self._dispatch(sender, msg, fun)
                    reply = RpcMessage(ok=True)
                    reply.update(val)
                    self._send(conn, reply)
                else:
                    self._send(conn, self.error("no such method"))
            except ValueError:
                self._send(conn, self.error("malformed message"))
             
        else:
            self.sel.unregister(conn)
            conn.close()

    @_checkReady
    def _dispatch(self, sender, msg, fun):

        # skip 'self' arg
        argnames = fun.__code__.co_varnames[1:]
        msg['sender'] = sender
        args = [msg[arg] for arg in argnames]
        return fun(self.app, *args)

    def Init(self, app):
        self.app = app
        self.iface, self.port = app.addr
        self.running = True
        self.killsock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sel.register(self.killsock, selectors.EVENT_READ, lambda f:3)

        self.sock = socket.socket()
        # TODO reuseaddr
        self.sock.bind((self.iface, self.port))
        self.sock.listen(10)
        self.sock.setblocking(False)

        self.sel.register(self.sock, selectors.EVENT_READ, acceptor(self))

        def run():
            while self.running:
                events = self.sel.select()
                for key, _ in events:
                    cb = key.data
                    cb(key.fileobj)
        self.t = Thread(target=run, name="RpcDispatcher %s:%s" % (self.iface, self.port))

        print("dispatcher started")
        self.t.start()


    def Method(self, f):
        
        self.funs[f.__name__] = f
        if __debug__:
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper
        return f


# TODO: add WS connection option
class RpcRemote(object):

    def __init__(self, addr):
        self.addr = addr

    def __getattr__(self, attr):
        ''' Override method calls -> magic '''
        return self._makeCaller(attr)

    def _call(self, addr, msg):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(addr)
            s.sendall(msg.Encode(ENC))
            data = s.recv(RECV_SIZE)
            s.close()
            return RpcMessage.Decode(data)
        except Exception as e:
            return RpcMessage(ok=False, msg=str(e))

    def _makeCaller(self, attr):
        def _caller(**kwargs):
            msg = RpcMessage(method=attr, **kwargs)
            return self._call(self.addr, msg)
        return _caller

    def __hash__(self):
        return self.addr.__hash__()

    @staticmethod
    def from_str(addr):
        host, port = parse_addr(addr)
        return RpcRemote((host, port))

    def __str__(self):
        return str(self.addr)


class RpcApplication(object, metaclass=GolangStyleImplLoaderMeta):

    def Start(self):
        Start()
        RpcModule.Init(self)

    #TODO: channel-based stopping mechanism
    def Stop(self):
        RpcModule.running = False
        RpcModule.t.join()
    
    def Kill(self):
        self.Stop()
        sys.exit(1)


# Public Singleton
def Start():
    global RpcModule

RpcModule = _RpcServer()
