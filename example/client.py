#!/usr/bin/env python3
import thinrpc
import logging
import sys

thinrpc.logger.setLevel(logging.DEBUG)
port = int(sys.argv[1])
rn = thinrpc.RpcRemote(("localhost", port))
print(rn.hello())
