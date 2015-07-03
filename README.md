thinrpc: A Lightweight RPC Framework for Python
===

This library provides a base class and some decorators to make it easy to build distributed applications. RPC endpoints are defined as class methods and decorated with ```RpcModule.Method```, which registers the endpoint with the event-based RPC server dispatching requests to registered methods. 

The ```RpcRemote``` class is an abstraction allowing applications to invoke methods on remote nodes using method call syntax. See the example below for an illustration!

```python
'''
    Simple RPC server responding to invocations of the
    'hello' method with a pleasant greeting
'''
import sys

from thinrpc import RpcModule, RpcRemote, RpcApplication, OK

class FooNode(RpcApplication):

    def __init__(self, port, name):
        self.addr = ("localhost", port)
        self.name = name

        # Start the RPC server
        self.Start()

    @RpcModule.Method
    def hello(self, sender):
        return OK, "Hi, %s! It's %s" % (sender, self.name)

    
if __name__ == '__main__':
    node = FooNode(9090, "Anson")
```

And now for a simple client script that invokes the ```hello``` method on the server application defined above.

```python

import thinrpc
import sys

# Say hi to the server!
server = thinrpc.RpcRemote(("localhost", 9090))
print(server.hello())
#{'result': "Hi, ('127.0.0.1', 49440)! It's Anson", 'err': False}
```
