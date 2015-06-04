#!/usr/bin/env python3
import sys

from pyrpc import RpcModule, RpcRemote



class FooNode(object):

    def __init__(self, port, name):
        self.name = name
        self.port = port
        RpcModule.Init(port, self)

    @RpcModule.Method
    def hello(self, sender) -> str:
        return "Hi, %s! It's %s" % (sender, self.name)

    
if __name__ == '__main__':
    port = int(sys.argv[1])
    node = FooNode(port, "boo")
