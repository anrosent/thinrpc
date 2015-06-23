#!/usr/bin/env python3
import pyrpc
import sys

port = int(sys.argv[1])
rn = pyrpc.RpcRemote(("localhost", port))
print(rn.hello())
