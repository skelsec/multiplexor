import websockets
import asyncio
import uuid
import json

from multiplexor.operator.protocol import OperatorCmdParser, OperatorLogEvent
from multiplexor.logger.logger import mpexception, Logger

class Operator:
	"""
	Represents an operator connection
	"""
	def __init__(self, websocket, operator_id, logQ):
		self.logger = Logger('Operator %s' % operator_id, logQ=logQ)
		self.websocket = websocket
		self.operator_id = operator_id
		self.multiplexor_cmd_in = asyncio.Queue()
		self.multiplexor_cmd_out = asyncio.Queue()
		self.transport_closed = asyncio.Event()
		self.incoming_task = None
		self.outgoing_task = None

	@mpexception
	async def handle_incoming_cmds(self):
		while self.websocket.open:
			try:
				data = await self.websocket.recv()
			except asyncio.CancelledError:
				return
			except websockets.exceptions.ConnectionClosed:
				self.transport_closed.set()
				return
			cmd = OperatorCmdParser.from_json(data)
			await self.multiplexor_cmd_in.put(cmd)
	
	@mpexception
	async def handle_outgoing_cmds(self):
		while self.websocket.open:
			try:
				cmd = await self.multiplexor_cmd_out.get()
				await self.websocket.send(json.dumps(cmd.to_dict()))
			except asyncio.CancelledError:
				return
			except Exception as e:
				await self.logger.error(e)
				return

	@mpexception
	async def terminate(self):
		self.incoming_task.cancel()
		self.outgoing_task.cancel()
		await self.websocket.close()

	@mpexception
	async def run(self):
		self.incoming_task = asyncio.create_task(self.handle_incoming_cmds())
		self.outgoing_task = asyncio.create_task(self.handle_outgoing_cmds())
		await self.websocket.wait_closed()
		await self.terminate()

	async def process_log(self, logmsg):
		if self.websocket.open:
			try:
				t = OperatorLogEvent()
				t.level = logmsg.level
				t.name = logmsg.name
				t.msg = logmsg.msg
				t.agent_id = logmsg.agent_id

				await self.websocket.send(json.dumps(t.to_dict()))
			except websockets.exceptions.ConnectionClosedError:
				return
			except Exception as e:
				await self.logger.exception()

class OperatorHandler:
	"""
	Creates a websocket server and listens for incoming operators, who will manage the agents via the server.
	Once a new operator connected, it will notify the server of the new operator, and channel the incoming/outgoing data
	"""
	def __init__(self, listen_ip, listen_port, logQ, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.sslctx = ssl_ctx
		self.transport_terminated_evt = asyncio.Event()
		
		self.operator_dispatch_queue = None		
		self.logger = Logger('multiplexor.operatorhandler', logQ = logQ)
		
	
	@mpexception
	async def handle_operator(self, websocket, path):
		await self.logger.debug('Operator connected!')
		
		operator = Operator(websocket, str(uuid.uuid4()), self.logger.logQ)
		await self.operator_dispatch_queue.put((operator, 'CONNECTED'))
		await operator.run()
		await self.logger.debug('Operator disconnected!')
		await self.operator_dispatch_queue.put((operator, 'DISCONNECTED'))

		
	@mpexception
	async def run(self):
		await self.logger.debug('Serving..')
		server = await websockets.serve(self.handle_operator, self.listen_ip, self.listen_port, ssl=self.sslctx)
		await server.wait_closed()
		self.transport_terminated_evt.set()