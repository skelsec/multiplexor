import asyncio
import enum

class MultiplexorPluginHandler:
	def __init__(self, plugin_id):
		self.plugin_id = plugin_id
		self.plugin_in_q = asyncio.Queue()
		self.plugin_out_q = asyncio.Queue()
		self.plugin_terminated_evt = asyncio.Event()
		
		self.plugin
		
class AgentStatus(enum.Enum):
	CONNECTED = 0,
	REGISTERING = 1,
	REGISTERED = 2,
	TERMINATING = 3,
	TERMINATED = 4
	
class MultiplexorAgentHandler:
	def __init__(self):
		self.agent_id = None
		self.cmd_send_queue = None
		self.cmd_recv_queue = None
		
		### internal stuff
		self.transport = None
		self.trasnport_terminated_evt = asyncio.Event()
		self.packetizer = None
		
		self.plugins = {}
		
		self.status = AgentStatus.CONNECTED
		
		self.info = None
		