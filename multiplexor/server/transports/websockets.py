import asyncio
import websockets
import uuid
from multiplexor.server.packetizer import Packetizer
from multiplexor.server.agent import MultiplexorAgent
from multiplexor.logger.logger import mpexception, Logger
	
		
class WebsocketsTransportServer:
	def __init__(self, listen_ip, listen_port, logging_queue, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.logger = Logger('WebsocketsTransportServer', logQ = logging_queue)
		self.agent_dispatch_queue = None #will be defined by the server!
		self.server = None

	@mpexception
	async def terminate(self):
		if self.server is not None:
			self.server.close()		
		if self.logger is not None:
			await self.logger.terminate()
	
	@mpexception
	async def handle_agent(self, websocket, path):
		"""
		This function gets invoked on each websocket connection.
		It creates an agenthandler with it's own packetizer, then notifies the server of the new agent's existense via the agent_dispatch_queue
		"""
		remote_ip, remote_port = websocket.remote_address
		await self.logger.info('Agent connected from %s:%s' % (remote_ip, remote_port))
		packetizer = Packetizer(self.logger.logQ) # packetizer must be created here, because it's parameters will change based on the transport!
		agent = MultiplexorAgent(self.logger.logQ, websocket, packetizer)
		await agent.run()
		await self.agent_dispatch_queue.put((agent, 'CONNECTED'))
		await agent.wait_closed()
		await self.logger.info('Agent disconnected! %s:%s' % (remote_ip, remote_port))
		await self.agent_dispatch_queue.put((agent, 'DISCONNECTED'))
		
	@mpexception
	async def run(self):
		self.server = await websockets.serve(self.handle_agent, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
		await self.server.wait_closed()