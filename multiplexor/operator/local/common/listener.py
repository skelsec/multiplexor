import asyncio
import websockets

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *


class MultiplexorOperatorListener:
	"""
	Listens for incoming traffic from the multiplexor server via the JS client
	be careful, this class will handle only one incoming server traffic!
	"""
	def __init__(self, listen_ip, listen_port, logQ, ssl_ctx = None, reconnect_interval = 5):
		self.logger = Logger("Connector", logQ)
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.reconnect_interval = reconnect_interval

		self.cmd_out_q = asyncio.Queue()
		self.cmd_in_q = asyncio.Queue()
		self.server_diconnected = asyncio.Event()
		self.ws = None


	async def cmd_in(self):
		while not self.server_diconnected.is_set():
			data = await self.ws.recv()
			rply = OperatorCmdParser.from_json(data)
			await self.cmd_in_q.put(rply)

	async def cmd_out(self):
		while not self.server_diconnected.is_set():
			cmd = await self.cmd_out_q.get()
			await self.ws.send(json.dumps(cmd.to_dict()))

	async def handle_server(self, ws, path):
		"""
		be careful, this class will handle only one incoming server traffic!
		"""
		if not self.server_diconnected.is_set():
			self.logger.error('Another proxy connection was initiated, but one is still active')
			return

		self.ws = ws
		await self.ws.wait_closed()
		await self.logger.info('Connection to server lost! Reconnect with your proxy again!')
		self.ws = None
		self.server_diconnected.set()

	async def run(self):
		while True:
			self.logger.info('Waiting for incoming connection!')
			server = await websockets.serve(self.handle_server, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
			await server.wait_closed()
			