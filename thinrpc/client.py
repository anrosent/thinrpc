import socket
from thinrpc import logger, ENC, RECV_SIZE, OK
from thinrpc.message import RpcMessage

# TODO: add WS connection option
class RpcRemote(object):

    def __init__(self, addr, timeout=None):
        self.addr = addr
        self.timeout = timeout

    def __getattr__(self, attr):
        ''' Override method calls -> magic '''
        return self._makeCaller(attr)

    def _call(self, addr, msg):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect(addr)
            s.sendall(msg.Encode(ENC))
            data = s.recv(RECV_SIZE)
            s.close()
            response = RpcMessage.Decode(data)
            if response.err:
                return RpcRemoteError(response.err), None
            else:
                return OK, response.result
        except Exception as e:
            return e, None

    def _makeCaller(self, attr):
        def _caller(**kwargs):
            logger.debug("[Server %s][Method %s][Args %s]", self.addr, attr, kwargs, extra={"mode":"client"})
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
