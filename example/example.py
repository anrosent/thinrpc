#!/usr/bin/env python3
import sys

from pyrpc import RpcModule, RpcRemote, RpcApplication

class FooNode(RpcApplication):

    def __init__(self, port, name):
        self.addr = ("localhost", port)
        self.name = name
        self.Start()

    @RpcModule.Method
    def hello(self, sender) -> str:
        return "Hi, %s! It's %s" % (sender, self.name)

    
if __name__ == '__main__':
    port = int(sys.argv[1])
    node = FooNode(port, "Anson")
