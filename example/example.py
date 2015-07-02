#!/usr/bin/env python3
import sys

import logging
from thinrpc import RpcModule, RpcRemote, RpcApplication, logger

logger.setLevel(logging.DEBUG)

class FooNode(RpcApplication):

    def __init__(self, port, name):
        self.addr = ("localhost", port)
        self.name = name
        self.Start(single_threaded=False)

    @RpcModule.Method
    def hello(self, sender) -> str:
        return "Hi, %s! It's %s" % (sender, self.name)

    
if __name__ == '__main__':
    port = int(sys.argv[1])
    node = FooNode(port, "Anson")
