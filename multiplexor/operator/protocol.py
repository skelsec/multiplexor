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
	PLUGIN_STARTED = 9
	PLUGIN_STOPPED = 10
	
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

class OperatorListAgentsCmd:
	def __init__(self):
		self.cmdtype = OperatorCmdType.LIST_AGENTS
		
	def to_dict(self):
		return {'cmdtype':self.cmdtype.value}
	
	@staticmethod
	def from_dict(d):
		return OperatorListAgentsCmd()
		
class OperatorListAgentsRply:
	def __init__(self):
		self.cmdtype = OperatorCmdType.LIST_AGENTS_RPLY
		self.agents = []
	
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agents' : self.agents,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListAgentsRply()
		for a in d['agents']:
			t.agents.append(a)
		return t
		
class OperatorGetAgentInfoCmd:
	def __init__(self):
		self.cmdtype = OperatorCmdType.GET_AGENT_INFO
		self.agent_id= None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetAgentInfoCmd()
		t.agent_id = d['agent_id']
		return t
		
class OperatorGetAgentInfoRply:
	def __init__(self):
		self.cmdtype = OperatorCmdType.GET_AGENT_INFO_RPLY
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
		t = OperatorGetAgentInfoRply()
		t.agent_id = d['agent_id']
		t.agentinfo = d['agentinfo']
		return t
		
class OperatorListPluginsCmd:
	def __init__(self):
		self.cmdtype = OperatorCmdType.GET_PLUGINS
		self.agent_id = None
		self.plugin_id = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'agentinfo' : self.agentinfo,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListPluginsCmd()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		return t
		
class OperatorListPluginsRply:
	def __init__(self):
		seld.cmdtype = OperatorCmdType.GET_PLUGINS_RPLY
		self.agent_id = None
		self.plugins = []
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugins' : self.plugins,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorListPluginsRply()
		t.agent_id = d['agent_id']
		t.plugins = d['plugins']
		return t
		
class OperatorGetPluginInfoCmd:
	def __init__(self):
		self.cmdtype = OperatorCmdType.GET_PLUGIN_INFO
		self.agent_id = None
		self.plugin_id = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetPluginInfoCmd()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		return t

class OperatorGetPluginInfoRply:
	def __init__(self):
		self.cmdtype = OperatorCmdType.GET_PLUGIN_INFO_RPLY
		self.agent_id = None
		self.plugin_id = None
		self.plugininfo = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
			'plugininfo' : self.plugininfo,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorGetPluginInfoRply()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		t.plugininfo = d['plugininfo']
		return t

class OperatorStartPlugin:
	def __init__(self):
		self.cmdtype = OperatorCmdType.START_PLUGIN
		self.agent_id = None
		self.plugin_type = None
		self.plugin_data = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_type' : self.plugin_type,
			'plugin_data' : self.plugin_data,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorStartPlugin()
		t.agent_id = d['agent_id']
		t.plugin_type = d['plugin_type']
		t.plugin_data = d['plugin_data']
		return t
		
class OperatorPluginStarted:
	def __init__(self):
		self.cmdtype = OperatorCmdType.PLUGIN_STARTED
		self.agent_id = None
		self.plugin_id = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_id,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorPluginStarted()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
		return t
		
class OperatorPluginStopped:
	def __init__(self):
		self.cmdtype = OperatorCmdType.PLUGIN_STOPPED
		self.agent_id = None
		self.plugin_id = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'agent_id' : self.agent_id,
			'plugin_id' : self.plugin_type,
		}
	
	@staticmethod
	def from_dict(d):
		t = OperatorPluginStarted()
		t.agent_id = d['agent_id']
		t.plugin_id = d['plugin_id']
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
	OperatorCmdType.PLUGIN_STARTED : OperatorPluginStarted,
	OperatorCmdType.PLUGIN_STOPPED : OperatorPluginStopped
}