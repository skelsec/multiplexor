import io
import enum

###
### TOTAL_LEN|CMD|VAR_CNT|LEN_VAR1|VAR1      |LEN_VAR2|VAR2
### 4        |1  |1      |4       |len(var_n)|4       |len(varn+1)....
###

class ServerCMDType(enum.Enum):
	REGISTER = 0
	GET_INFO = 1
	SWITCH_ENCRYPTION = 2
	START_ENCRYPTION = 3
	PLUGIN_START = 4
	PLUGIN_STOP = 5
	PLUGIN_DATA = 6
	PLUGIN_STOPPED_EVT = 7
	PLUGIN_STARTED_EVT = 8
	AGENT_LOG = 9
	
class MultiplexorGetInfo:
	def __init__(self):
		self.cmdtype = ServerCMDType.GET_INFO
		self.agent_id = None
		self.agent_info = None
		
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorGetInfo()
		p.agent_id = cmd.params[0].decode()
		p.agent_info = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		if self.agent_info:
			cmd.params.append(self.agent_id.encode())
			cmd.params.append(self.agent_info.encode())			
		return cmd.to_bytes()
	
class MultiplexorRegister:
	def __init__(self):
		self.cmdtype = ServerCMDType.REGISTER
		self.secret = None
		self.agent_id = None
		
		
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorRegister()
		if len(cmd.params) != 0:
			p.secret = cmd.params[0]
			if len(cmd.params) > 1:
				p.agent_id = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.secret)
		if self.agent_id:
			cmd.params.append(self.agent_id.encode())
		return cmd.to_bytes()
	
class MultiplexorPluginStart:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_START
		self.plugin_type = None
		self.plugin_id = None
		self.plugin_params = []
		
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorPluginStart()
		p.plugin_type = cmd.params[0].decode()
		if len(cmd.params) > 0:
			p.plugin_id = cmd.params[1].decode()
		if len(cmd.params) > 1:
			for i in range(2, cmd.params):
				p.plugin_params.append(cmd.params[i].decode())
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.plugin_type.encode())
		if self.plugin_id:
			cmd.params.append(self.plugin_id.encode())
			if self.plugin_params:
				for p in self.plugin_params:
					cmd.params.append(p.encode())
		return cmd.to_bytes()
		
class MultiplexorPluginStop:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_STOP
		self.plugin_id = None
		
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorPluginStop()
		p.plugin_id = cmd.params[0].decode()
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.plugin_id.encode())
		return cmd.to_bytes()
		
class MultiplexorPluginData:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_DATA
		self.plugin_id = None
		self.plugin_data = None #bytes!
	
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorPluginData()
		p.plugin_id = cmd.params[0].decode()
		p.plugin_data = cmd.params[1]
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.plugin_id.encode())
		cmd.params.append(self.plugin_data)
		return cmd.to_bytes()

class MultiplexorPluginStoppedEvt:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_STOPPED_EVT
		self.plugin_id = None
		self.reason = None
	
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorPluginStoppedEvt()
		p.plugin_id = cmd.params[0].decode()
		p.reason = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.plugin_id.encode())
		cmd.params.append(self.reason.encode())
		return cmd.to_bytes()
		
class MultiplexorPluginStartedEvt:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_STARTED_EVT
		self.plugin_id = None
	
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorPluginStartedEvt()
		p.plugin_id = cmd.params[0].decode()
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.plugin_id.encode())
		return cmd.to_bytes()
		
class MultiplexorAgentLog:
	def __init__(self):
		self.cmdtype = ServerCMDType.AGENT_LOG
		self.severity = None
		self.msg = None
		self.plugin_id = None
		
	
	@staticmethod
	def from_cmd(cmd):
		p = MultiplexorAgentLog()
		p.severity = int.from_bytes(cmd.params[0], 'big', signed = False)
		p.msg = cmd.params[1].decode()
		p.plugin_id = int.from_bytes(cmd.params[2], 'big', signed = False)
		return p
		
	def to_bytes(self):
		cmd = MultiplexorCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.severity.to_bytes(4, 'big', signed = False))
		cmd.params.append(self.msg.encode())
		cmd.params.append(self.plugin_id.to_bytes(4, 'big', signed = False))
		return cmd.to_bytes()
		

class MultiplexorCMD:
	def __init__(self):
		self.cmdtype = None
		self.params = []
	
	@staticmethod
	def from_string(data):
		return MultiplexorCMD.from_bytes(bytes.fromhex(data))
		
	@staticmethod
	def from_bytes(data):
		return MultiplexorCMD.from_buffer(io.BytesIO(data))
		
	@staticmethod
	def from_buffer(buff):
		cmd = MultiplexorCMD()
		cmd.cmdtype = ServerCMDType(buff.read(1)[0])
		param_len = buff.read(1)[0]
		for i in range(param_len):
			plen = int.from_bytes(buff.read(4), 'big', signed = False)
			cmd.params.append(buff.read(plen))
			
		if cmd.cmdtype in type2obj and type2obj[cmd.cmdtype]:
			return type2obj[cmd.cmdtype].from_cmd(cmd)
		return cmd
		
	def to_bytes(self):
		t = self.cmdtype.value.to_bytes(1, 'big', signed = False)
		t += len(self.params).to_bytes(1, 'big', signed = False)
		for i in range(len(self.params)):
			t += len(self.params[i]).to_bytes(4, 'big', signed = False)
			t += self.params[i]
		return t
		
	def to_string(self):
		return self.to_bytes().hex()
		
	def __str__(self):
		t = '==== MultiplexorCMD ====\r\n'
		t += 'cmdtype: %s\r\n' % self.cmdtype.name
		for i, val in enumerate(self.params):
			t += 'var%s: %s\r\n' % (i, val)
		
		return t
		
		
type2obj = {
	ServerCMDType.REGISTER : MultiplexorRegister,
	ServerCMDType.GET_INFO : MultiplexorGetInfo,
	ServerCMDType.SWITCH_ENCRYPTION : None, #TODO: implement
	ServerCMDType.START_ENCRYPTION : None, #TODO: implement
	ServerCMDType.PLUGIN_START : MultiplexorPluginStart,
	ServerCMDType.PLUGIN_STOP : MultiplexorPluginStop,
	ServerCMDType.PLUGIN_DATA : MultiplexorPluginData,
	ServerCMDType.PLUGIN_STOPPED_EVT : MultiplexorPluginStoppedEvt,
	ServerCMDType.PLUGIN_STARTED_EVT : MultiplexorPluginStartedEvt,
	ServerCMDType.AGENT_LOG : MultiplexorAgentLog,
}