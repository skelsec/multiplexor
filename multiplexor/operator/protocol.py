import json
import enum

class OperatorCmdType(enum.Enum):
	LIST_AGENTS = 0
	LIST_AGENTS_RPLY = 1
	GET_AGENT_INFO = 2
	GET_AGENT_INFO_RPLY = 3
	GET_PLUGINS = 4
	GET_PLUGINS_RPLY = 5
	GET_PLUGIN_INFO = 6
	GET_PLUGIN_INFO_RPLY = 7
	START_PLUGIN = 8
	PLUGIN_STARTED_EVT = 9
	PLUGIN_STOPPED_EVT = 10
	LOG_EVT = 11
	PLUGIN_DATA_EVT = 12
	EXCEPTION = 13
	START_PLUGIN_RPLY = 14
	AGENT_CONNECTED_EVT = 15
	AGENT_DISCONNECTED_EVT = 16

class OperatorCmdParser:
	
	@staticmethod
	def from_json(jd):
		return OperatorCmdParser.from_dict(json.loads(jd))
		
	@staticmethod
	def from_dict(d):
		if 'cmdtype' not in d:
			raise Exception('Unknown data!')
		
		t = OperatorCmdType(d['cmdtype'])
		if t not in type2obj:
			raise Exception('Object not found!')
		
		return type2obj[t].from_dict(d)

class OperatorExceptionEvt:
	def __init__(self, cmd_id = None, exc_data = None):
		self.cmdtype = OperatorCmdType.EXCEPTION
		self.cmd_id = cmd_id
		self.exc_data = exc_data
		
	def to_dict(self):
		return {
			'cmdtype':self.cmdtype.value,
			'cmd_id': self.cmd_id,
			'exc_data': self.exc_data
		}
	
	@staticmethod
	def from_dict(d):
		return OperatorExceptionEvt(cmd_id = d['cmd_id'], exc_data = d['exc_data'])

class OperatorListAgentsCmd:
	def __init__(self, cmd_id = None):
		self.cmdtype = OperatorCmdType.LIST_AGENTS
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype':self.cmdtype.value,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		return OperatorListAgentsCmd(cmd_id = d['cmd_id'])

class OperatorLogEvent:
	def __init__(self):
		self.cmdtype = OperatorCmdType.LOG_EVT
		self.level = None
		self.name = None
		self.msg = None
		self.agent_id = None
	
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'level' : self.level,
			'name' : self.name,
			'msg' : self.msg,
			'agent_id' : self.agent_id,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorLogEvent()
		t.level = d['level']
		t.name = d['name']
		t.msg = d['msg']
		t.agent_id = d['agent_id']
		return t
		
class OperatorListAgentsRply:
	def __init__(self, cmd_id = None):
		self.cmdtype = OperatorCmdType.LIST_AGENTS_RPLY
		self.cmd_id = cmd_id
		self.agents = []
	
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agents' : self.agents,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListAgentsRply(cmd_id = d['cmd_id'])
		for a in d['agents']:
			t.agents.append(a)
		return t
		
class OperatorGetAgentInfoCmd:
	def __init__(self, cmd_id = None, agent_id = None):
		self.cmdtype = OperatorCmdType.GET_AGENT_INFO
		self.agent_id= agent_id
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetAgentInfoCmd(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		return t
		
class OperatorGetAgentInfoRply:
	def __init__(self, cmd_id = None):
		self.cmdtype = OperatorCmdType.GET_AGENT_INFO_RPLY
		self.agent_id = None
		self.agentinfo = None
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'agentinfo' : self.agentinfo,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetAgentInfoRply(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		t.agentinfo = d['agentinfo']
		return t
		
class OperatorListPluginsCmd:
	def __init__(self, cmd_id = None, agent_id = None):
		self.cmdtype = OperatorCmdType.GET_PLUGINS
		self.agent_id = agent_id
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListPluginsCmd(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		return t
		
class OperatorListPluginsRply:
	def __init__(self, cmd_id = None):
		self.cmdtype = OperatorCmdType.GET_PLUGINS_RPLY
		self.agent_id = None
		self.plugins = []
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugins' : self.plugins,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListPluginsRply(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		t.plugins = d['plugins']
		return t
		
class OperatorGetPluginInfoCmd:
	def __init__(self, cmd_id=None, agent_id = None, plugin_id = None):
		self.cmdtype = OperatorCmdType.GET_PLUGIN_INFO
		self.agent_id = agent_id
		self.plugin_id = plugin_id
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetPluginInfoCmd(cmd_id =d['cmd_id'])
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		return t

class OperatorGetPluginInfoRply:
	def __init__(self, cmd_id=None):
		self.cmdtype = OperatorCmdType.GET_PLUGIN_INFO_RPLY
		self.agent_id = None
		self.plugin_id = None
		self.plugininfo = None
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'plugininfo' : self.plugininfo,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetPluginInfoRply(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		t.plugininfo = d['plugininfo']
		return t

class OperatorStartPlugin:
	def __init__(self, cmd_id = None, agent_id = None, plugin_type = None, plugin_data = None, operator_token = None):
		self.cmdtype = OperatorCmdType.START_PLUGIN
		self.agent_id = agent_id
		self.plugin_type = plugin_type
		self.cmd_id = cmd_id
		self.operator_token = operator_token
		
		self.server = {} #startup parameters for the multiplexor server
		self.agent = {} #startup parameters for the remote agent
		
		#self.operator_token = operator_token #operator token is there to identify the plugin creation success/failure
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_type' : self.plugin_type,
			'server' : self.server.to_dict() if self.server else None,
			'agent' : self.agent.to_dict() if self.agent else None,
			'cmd_id': self.cmd_id,
			'operator_token' : self.operator_token

		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorStartPlugin()
		t.cmd_id = d['cmd_id']
		t.agent_id = d['agent_id']
		t.plugin_type = d['plugin_type']
		t.operator_token = d['operator_token']
		t.server = d.get('server') if d.get('server') else None
		t.agent = d.get('agent') if d.get('agent') else None
		return t

class OperatorStartPluginRply:
	def __init__(self, cmd_id=None):
		self.cmdtype = OperatorCmdType.START_PLUGIN_RPLY
		self.agent_id = None
		self.plugin_id = None
		self.cmd_id = cmd_id
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'cmd_id': self.cmd_id
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetPluginInfoRply(cmd_id = d['cmd_id'])
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		return t
		
class OperatorPluginStartedEvt:
	def __init__(self):
		self.cmdtype = OperatorCmdType.PLUGIN_STARTED_EVT
		self.agent_id = None
		self.plugin_id = None
		self.operator_token = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'operator_token' : self.operator_token,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorPluginStartedEvt()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		t.operator_token = d['operator_token']
		return t
		
class OperatorPluginStoppedEvt:
	def __init__(self):
		self.cmdtype = OperatorCmdType.PLUGIN_STOPPED_EVT
		self.agent_id = None
		self.plugin_id = None
		self.operator_token = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'operator_token' : self.operator_token,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorPluginStoppedEvt()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		t.operator_token = d['operator_token']
		return t

class OperatorPluginData:
	def __init__(self, agent_id = None, plugin_id = None, data = None):
		self.cmdtype = OperatorCmdType.PLUGIN_DATA_EVT
		self.agent_id = agent_id
		self.plugin_id = plugin_id
		self.data = data
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'data' : self.data,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorPluginData()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		t.data = d['data']
		return t

class OperatorAgentConnectedEvt:
	def __init__(self):
		self.cmdtype = OperatorCmdType.AGENT_CONNECTED_EVT
		self.agent_id = None
		self.agentinfo = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'agentinfo' : self.agentinfo,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorAgentConnectedEvt()
		t.agent_id = d['agent_id']
		t.agentinfo = d['agentinfo']
		return t

class OperatorAgentDisconnectedEvt:
	def __init__(self):
		self.cmdtype = OperatorCmdType.AGENT_DISCONNECTED_EVT
		self.agent_id = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorAgentDisconnectedEvt()
		t.agent_id = d['agent_id']
		return t
		
type2obj = {
	OperatorCmdType.LIST_AGENTS : OperatorListAgentsCmd,
	OperatorCmdType.LIST_AGENTS_RPLY : OperatorListAgentsRply,
	OperatorCmdType.GET_AGENT_INFO : OperatorGetAgentInfoCmd,
	OperatorCmdType.GET_AGENT_INFO_RPLY : OperatorGetAgentInfoRply,
	OperatorCmdType.GET_PLUGINS : OperatorListPluginsCmd,
	OperatorCmdType.GET_PLUGINS_RPLY : OperatorListPluginsRply,
	OperatorCmdType.GET_PLUGIN_INFO : OperatorGetPluginInfoCmd,
	OperatorCmdType.GET_PLUGIN_INFO_RPLY : OperatorGetPluginInfoRply,
	OperatorCmdType.START_PLUGIN : OperatorStartPlugin,
	OperatorCmdType.PLUGIN_STARTED_EVT : OperatorPluginStartedEvt,
	OperatorCmdType.PLUGIN_STOPPED_EVT : OperatorPluginStoppedEvt,
	OperatorCmdType.PLUGIN_DATA_EVT : OperatorPluginData,
	OperatorCmdType.LOG_EVT : OperatorLogEvent,
	OperatorCmdType.EXCEPTION : OperatorExceptionEvt,
	OperatorCmdType.START_PLUGIN_RPLY : OperatorStartPluginRply,
	OperatorCmdType.AGENT_CONNECTED_EVT : OperatorAgentConnectedEvt,
	OperatorCmdType.AGENT_DISCONNECTED_EVT : OperatorAgentDisconnectedEvt,
}