import json

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

