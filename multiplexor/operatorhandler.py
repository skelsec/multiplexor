import websockets
import asyncio

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *

class OperatorHandler:
	def __init__(self, listen_ip, listen_port, logQ, sslctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.sslctx = sslctx
		
		self.multiplexor_cmd_in = asyncio.Queue()
		self.multiplexor_cmd_out = asyncio.Queue()
		
		self.transport_closed = asyncio.Event()
		
		self.logger = Logger('OperatorHandler', logQ = logQ)
		
	@mpexception
	async def handle_incoming_cmds(self, websocket):
		while not self.transport_closed.is_set():
			print('waiting on data')
			data = await websocket.recv()
			print(data)
			cmd = OperatorCmdParser.from_json(data)
			await self.multiplexor_cmd_in.put(cmd)
	
	@mpexception
	async def handle_outgoing_cmds(self, websocket):
		while not self.transport_closed.is_set():
			cmd = await self.multiplexor_cmd_out.get()
			await websocket.send(json.dumps(cmd.to_dict()))

	@mpexception
	async def handle_operator(self, websocket, path):
		await self.logger.debug('Operator connected!')
		
		asyncio.ensure_future(self.handle_incoming_cmds(websocket))
		asyncio.ensure_future(self.handle_outgoing_cmds(websocket))
		await websocket.wait_closed()
		self.transport_closed.set()
		await self.logger.debug('Operator disconnected!')
		
	@mpexception
	async def run(self):
		try:
			await self.logger.debug('Serving..')
			server = await websockets.serve(self.handle_operator, self.listen_ip, self.listen_port, ssl=self.sslctx)
			await server.wait_closed()
		except Exception as e:
			print(e)