import enum

class Socks5ServerCmdType(enum.Enum):
	PLUGIN_CONNECT = 0
	PLUGIN_LISTEN = 1
	PLUGIN_UDP = 2
	PLUGIN_ERROR = 3
	SOCKET_TERMINATED_EVT = 4
	SOCKET_DATA = 5
	
	
class Socks5PluginConnectCmd:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_CONNECT
		self.dst_addr = None
		self.dst_port = None
	
	@staticmethod
	def from_cmd(cmd):
		p = Socks5PluginConnectCmd()
		p.dst_addr = cmd.params[0].decode()
		p.dst_port = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = Socks5PluginConnectCmd()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.dst_addr.encode())
		cmd.params.append(self.dst_port.encode())
		return cmd.to_bytes()
		
class Socks5PluginListenCmd:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_LISTEN
		self.listen_addr = None
		self.listen_port = None
	
	@staticmethod
	def from_cmd(cmd):
		p = Socks5PluginListenCmd()
		p.listen_addr = cmd.params[0].decode()
		p.listen_port = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = Socks5PluginListenCmd()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.listen_addr.encode())
		cmd.params.append(self.listen_port.encode())
		return cmd.to_bytes()
		
class Socks5PluginUDPCmd:
	def __init__(self):
		self.cmdtype = ServerCMDType.PLUGIN_UDP
		self.listen_addr = None
		self.listen_port = None
	
	@staticmethod
	def from_cmd(cmd):
		p = Socks5PluginUDPCmd()
		p.listen_addr = cmd.params[0].decode()
		p.listen_port = cmd.params[1].decode()
		return p
		
	def to_bytes(self):
		cmd = Socks5PluginUDPCmd()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.listen_addr.encode())
		cmd.params.append(self.listen_port.encode())
		return cmd.to_bytes()
		
class Socks5PluginSocketDataCmd:
	def __init__(self):
		self.cmdtype = ServerCMDType.SOCKET_DATA
		self.data = None
	
	@staticmethod
	def from_cmd(cmd):
		p = Socks5PluginSocketDataCmd()
		p.data = cmd.params[0]
		return p
		
	def to_bytes(self):
		cmd = Socks5PluginSocketDataCmd()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.data)
		return cmd.to_bytes()
		
class Socks5PluginSocketTerminatedEvent:
	def __init__(self):
		self.cmdtype = ServerCMDType.SOCKET_TERMINATED_EVT
	
	@staticmethod
	def from_cmd(cmd):
		p = Socks5PluginSocketTerminatedEvent()
		return p
		
	def to_bytes(self):
		cmd = Socks5PluginSocketTerminatedEvent()
		return cmd.to_bytes()
	
class Socks5PluginCMD:
	def __init__(self):
		self.cmdtype = None
		self.params = []
	
	@staticmethod
	def from_string(data):
		return Socks5PluginCMD.from_bytes(bytes.fromhex(data))
		
	@staticmethod
	def from_bytes(data):
		return Socks5PluginCMD.from_buffer(io.BytesIO(data))
		
	@staticmethod
	def from_buffer(buff):
		cmd = Socks5PluginCMD()
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
		t = '==== Socks5PluginCMD ====\r\n'
		t += 'cmdtype: %s\r\n' % self.cmdtype.name
		for i, val in enumerate(self.params):
			t += 'var%s: %s\r\n' % (i, val)
		
		return t

type2obj = {
	Socks5ServerCmdType.PLUGIN_CONNECT : Socks5PluginConnectCmd,
	Socks5ServerCmdType.SOCKET_DATA : Socks5PluginSocketDataCmd,
	Socks5ServerCmdType.SOCKET_TERMINATED_EVT : Socks5PluginSocketTerminatedEvent,
	Socks5ServerCmdType.PLUGIN_LISTEN : Socks5PluginListenCmd,
	Socks5ServerCmdType.PLUGIN_UDP : Socks5PluginUDPCmd,
}