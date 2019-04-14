import asyncio
import websockets

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
		self.server_connected = asyncio.Event() #this variable is used to signel status towards the modules

	@mpexception
	async def cmd_in(self, ws):
		while ws and ws.open:
			data = await ws.recv()
			cmd = OperatorCmdParser.from_json(data)
			await self.cmd_in_q.put(cmd)

	@mpexception
	async def cmd_out(self, ws):
		while ws and ws.open:
			rply = await self.cmd_out_q.get()
			await ws.send(json.dumps(rply.to_dict()))


	async def run(self):
		while True:
			await self.logger.info('Connecting to server')
			try:
				ws = await websockets.connect(self.server_url)
				asyncio.ensure_future(self.cmd_in(ws))
				asyncio.ensure_future(self.cmd_out(ws))
				self.server_connected.set()
				await ws.wait_closed()
				self.server_connected.clear()
				
			except Exception as e:
				await self.logger.info('Error connecting to server! Reason: %s' % e)
			else:
				await self.logger.info('Connection lost to server! Reconnecting in %s seconds' % self.reconnect_interval)
			await asyncio.sleep(self.reconnect_interval)