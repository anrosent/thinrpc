import socket
import selectors
import types
import os
import sys
import imp
import json
import logging

from urllib.parse import splitnport as parse_addr
from threading import Thread

from thinrpc.message import RpcMessage
from thinrpc.client import RpcRemote
from thinrpc import logger, RECV_SIZE, ENC

OK = False


################################################################################

# TODO: more robust insertion of sender
# TODO: pass (Err, result) up to RpcRemote impl so clients can just unpack/test
# TODO: dynamic namedtuple for 'result' vals
# TODO: better logging solution for "extra" param (wrapper)
# TODO: refactor components into separate modules

def single_threaded_acceptor(srv):
    def handle_new_conn(sock):
        conn, addr = sock.accept()
        conn.setblocking(False)
        srv.sel.register(conn, selectors.EVENT_READ, srv._handle)
    return handle_new_conn

def single_threaded_destructor(srv, conn):
    srv.sel.unregister(conn)
    conn.close()

def multi_threaded_destructor(srv, conn):
    conn.close()


def multi_thread_handler(srv, conn):
    while True:
        shutdown = srv._handle(conn)
        if shutdown:
            break

def multi_threaded_acceptor(srv):
    def handle_new_conn(sock):
        conn, addr = sock.accept()
        Thread(target=multi_thread_handler, args=[srv, conn]).start()
    return handle_new_conn

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

class _RpcServer(object):
    running = False
    enc = "json"
    sel = selectors.DefaultSelector()
    funs = {}
    
    # error check
    def error(self, msg):
        return RpcMessage(err=msg)

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
        logger.debug("Received data '%s' from client %s", data, sender, extra={"mode":"server"})
        if data:
            try:
                msg = RpcMessage.Decode(data) 
                method = msg["method"]
                logger.debug("[Client %s][Method %s][Msg %s]", sender, method, msg, extra={"mode":"server"})
                if method in self.funs:
                    fun = self.funs[method]

                    err, val = self._dispatch(sender, msg, fun)
                    logger.debug("[Client %s][Method %s][Result %s]", sender, method, val, extra={"mode":"server"})
                    reply = RpcMessage(err=err, result=val)
                    self._send(conn, reply)
                else:
                    logger.debug("[Client %s][Method %s][NoSuchMethod]", sender, method, extra={"mode":"server"})
                    self._send(conn, self.error("no such method"))
            except ValueError as e:
                self._send(conn, self.error("malformed message: %s" % str(e)))
                logger.debug("[Client %s][Method %s][BadMsg %s]", sender, method, msg, extra={"mode":"server"})
             
        else:
            self.conn_destructor(self, conn)
            return True

    @_checkReady
    def _dispatch(self, sender, msg, fun):

        # skip 'self' arg
        argnames = fun.__code__.co_varnames[1:fun.__code__.co_argcount]

        msg['sender'] = sender
        args = [msg[arg] for arg in argnames]
        return fun(self.app, *args)

    def Init(self, app, single_threaded=True):
        logger.info("Starting server on %s, single_threaded=%s", app.addr, single_threaded, extra={"mode":"server"})
        self.app = app
        self.iface, self.port = app.addr
        self.running = True
        self.killsock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sel.register(self.killsock, selectors.EVENT_READ, lambda f:3)
        
        if single_threaded:
            self.acceptor = single_threaded_acceptor
            self.conn_destructor = single_threaded_destructor
        else:
            self.acceptor = multi_threaded_acceptor
            self.conn_destructor = multi_threaded_destructor

        self.sock = socket.socket()
        # TODO reuseaddr
        self.sock.bind((self.iface, self.port))
        self.sock.listen(10)
        self.sock.setblocking(False)

        self.sel.register(self.sock, selectors.EVENT_READ, self.acceptor(self))

        def run():
            logger.info("Server started", extra={"mode":"server"})
            while self.running:
                events = self.sel.select()
                for key, _ in events:
                    cb = key.data
                    cb(key.fileobj)
        self.t = Thread(target=run, name="RpcDispatcher %s:%s" % (self.iface, self.port))
        self.t.start()


    def Method(self, f):
        
        self.funs[f.__name__] = f
        return f

class RpcApplication(object, metaclass=GolangStyleImplLoaderMeta):

    def Start(self, **kwargs):
        RpcModule.Init(self, **kwargs)

    #TODO: channel-based stopping mechanism
    def Stop(self):
        logger.info("Stopping RPC server....", extra={"mode":"server"})
        RpcModule.running = False
        RpcModule.t.join()
        logger.info("Server stopped", extra={"mode":"server"})
    
    def Kill(self):
        self.Stop()
        logger.info("Exiting...", extra={"mode":"server"})
        sys.exit(1)

RpcModule = _RpcServer()
