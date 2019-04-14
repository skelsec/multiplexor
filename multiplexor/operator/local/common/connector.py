import asyncio
import weboskcets

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *


class MultiplexorOperatorConnector:
	def __init__(self, server_url, logQ, ssl_ctx = None, reconnect_interval = 5):
		self.logger = Logger("Connector", logQ)
		self.server_url = server_url
		self.ssl_ctx = ssl_ctx
		self.reconnect_interval = reconnect_interval

		self.cmd_out_q = asyncio.Queue()
		self.cmd_in_q = asyncio.Queue()
		self.server_diconnected = asyncio.Event()
		self.ws = None


	async def cmd_in(self):
		while not self.server_diconnected.is_set():
			data = await self.ws.recv()
			cmd = 
			await self.cmd_in_q.put(cmd)

	async def cmd_out(self):
		while not self.server_diconnected.is_set():
			rply = await self.cmd_out_q.get()
			await self.ws.send(json.dumps(rply.to_dict()))


	async def run(self):
		while True:
			self.logger.info('Connecting to server')
			self.ws = await websockets.connect(self.server_url)
			self.logger.info('Connection lost to server! Reconnecting in %s seconds' % self.reconnect_interval)
			asyncio.sleep(self.reconnect_interval)