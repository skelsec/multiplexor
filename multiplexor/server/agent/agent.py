import asyncio
import enum

from multiplexor.logger.logger import mpexception, Logger
from multiplexor.server.protocol import MultiplexorPluginData
		
class AgentStatus(enum.Enum):
	CONNECTED = 0
	REGISTERING = 1
	REGISTERED = 2
	TERMINATING = 3
	TERMINATED = 4
	
class MultiplexorAgent:
	def __init__(self, logQ, transport, packetizer):
		self.logger = Logger('MultiplexorAgent', logQ)
		self.agent_id = None
		self.teminated_evt = asyncio.Event()
		self.transport = transport
		self.packetizer = packetizer
		
		self.plugin_ctr = 0
		self.plugins = {}
		self.plugin_taks = {}
		self.plugin_operator = {} #plugin_id -> operator
		
		self.status = AgentStatus.CONNECTED
		
		self.info = None

		self.packetizer_task = None
		self.packetizer_send_task = None
		self.packetizer_recv_task = None


	@mpexception	
	async def handle_packetizer_send(self):
		"""
		Gets raw bytes from the packetizer and sends it to the agent
		"""
		while True:
			data = await self.packetizer.packetizer_out.get()
			# uncomment this for print of outgoing data
			#print('handle_packetizer_send %s' % data)
			try:
				await self.transport.send(data)
			except Exception as e:
				await self.logger.debug('handle_packetizer_send %s' % e)
				await self.terminate()
				return

	@mpexception	
	async def handle_packetizer_recv(self):
		"""
		Dispatches the data recieved from the agent to the packetizer
		"""
		while True:
			try:
				data = await self.transport.recv()
				# uncomment this for print of incoming data
				#print('handle_packetizer_recv' % data)
			except asyncio.CancelledError:
				return

			except Exception as e:
				await self.logger.debug('handle_packetizer_send %s' % e)
				await self.terminate()
				return
			else:
				await self.packetizer.packetizer_in.put(data)

	@mpexception	
	async def run(self):
		await self.packetizer.run()
		self.packetizer_send_task = asyncio.create_task(self.handle_packetizer_send())
		self.packetizer_recv_task = asyncio.create_task(self.handle_packetizer_recv())


	@mpexception
	async def wait_closed(self):
		await self.teminated_evt.wait()

	@mpexception
	async def terminate(self):
		if self.transport:
			await self.transport.close()
		if self.packetizer is not None:
			await self.packetizer.terminate()
		if self.packetizer_send_task is not None:
			self.packetizer_send_task.cancel()
		if self.packetizer_recv_task is not None:
			self.packetizer_recv_task.cancel()

		for plugin_id in self.plugins:
			await self.plugins[plugin_id].terminate()
		for plugin_id in self.plugin_taks:
			self.plugin_taks[plugin_id].cancel()

		await self.logger.terminate()
		self.teminated_evt.set()
		
		
	@mpexception
	async def handle_plugin_out(self, plugin):
		"""
		This function created one per new plugin started
		All it does is to wrap the plugin's outgoing bytes to a server command 
		then dispatches it to the agent's packetizer
		"""
		while not plugin.stop_plugin_evt.is_set():
			data = await plugin.plugin_out.get() #bytes!
			
			cmd = MultiplexorPluginData()
			cmd.plugin_id = plugin.plugin_id
			cmd.plugin_data = data
			await self.packetizer.multiplexor_out.put(cmd)
			await asyncio.sleep(0)
		#at this pont the plugin stopped / agent disconnected
		del self.plugins[plugin.plugin_id]		
		
	def add_plugin(self, plugin_obj, cmd, operator):
		plugin_id = str(self.plugin_ctr)
		self.plugin_ctr += 1
		self.plugin_operator[plugin_id] = operator
		self.plugins[plugin_id] = plugin_obj(plugin_id, self.logger.logQ, cmd.plugin_type, cmd.server)
		self.plugin_taks[plugin_id] = asyncio.create_task(self.handle_plugin_out(self.plugins[plugin_id]))
		return plugin_id