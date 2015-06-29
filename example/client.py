#!/usr/bin/env python3
import thinrpc
import sys

port = int(sys.argv[1])
rn = thinrpc.RpcRemote(("localhost", port))
print(rn.hello())
