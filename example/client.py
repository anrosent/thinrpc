#!/usr/bin/env python3
import logging
import sys
import thinrpc
import thinrpc.client as client

thinrpc.logger.setLevel(logging.DEBUG)
port = int(sys.argv[1])
rn = client.RpcRemote(("localhost", port))
print(rn.hello())
