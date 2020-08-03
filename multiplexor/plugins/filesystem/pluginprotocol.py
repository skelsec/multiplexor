import enum
import io

"""
All command parameters are sent as string or None
"""

class FSCmdType(enum.Enum):
	CONNECT = 0,
	TERMINATED = 1,
	OK = 2,
	ERR = 3,
	LIST = 4,
	FILE_INFO = 5,
	GET_FILE = 6,
	FILE_DATA = 7,


def eon(x):
	"""
	encode or none
	"""
	if not x:
		return x
	return x.encode()
	
def don(x):
	"""
	decode or none
	"""
	if not x:
		return x
	return x.decode()
	
class FSCMDError:
	def __init__(self):
		self.cmdtype = FSCmdType.ERR
		self.session_id = None
		self.token = None
		self.reason = None

	def get_exception(self):
		return Exception('Filesystem operation error! Reason : %s' % self.reason)

	@staticmethod
	def from_cmd(cmd):
		p = FSCMDError()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		p.reason = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
			'reason' : self.reason ,	
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDError()
		c.token = d['token']
		c.reason = d['reason']
		
		return c
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.reason)
		return cmd.to_bytes()
		
class FSCMDConnect:
	def __init__(self):
		self.cmdtype = FSCmdType.CONNECT
		self.session_id = None
	
	@staticmethod
	def from_cmd(cmd):
		p = FSCMDConnect()
		p.session_id = cmd.params[0]
		return p
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		return cmd.to_bytes()

class FSCMDTerminate:
	def __init__(self):
		self.cmdtype = FSCmdType.TERMINATED
		self.session_id = None
	
	@staticmethod
	def from_cmd(cmd):
		p = FSCMDTerminate()
		p.session_id = cmd.params[0]
		return p

	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'session_id' : self.session_id ,
		}
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		return cmd.to_bytes()

	@staticmethod
	def from_dict(d):
		c = FSCMDTerminate()
		c.session_id = d['session_id']		
		return c


		
class FSCMDOK:
	def __init__(self):
		self.cmdtype = FSCmdType.OK
		self.session_id = None
		self.token = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token,
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDOK()
		c.token = d['token']
		
		return c
	
	@staticmethod
	def from_cmd(cmd):
		p = FSCMDOK()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		return p
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		return cmd.to_bytes()
		
class FSCMDList:
	def __init__(self):
		self.cmdtype = FSCmdType.LIST
		self.session_id = None
		self.token = None
		self.path = None
		self.filter = None

	@staticmethod
	def from_cmd(cmd):
		p = FSCMDList()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		p.path = cmd.params[2]
		p.filter = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
			'path' : self.path ,
			'filter' : self.filter ,
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDList()
		c.token = d.get('token')
		c.path = d.get('path')
		c.filter = d.get('filter')
		
		return c
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		cmd.params.append(self.path)
		cmd.params.append(self.filter)
		return cmd.to_bytes()
		
class FSCMDFileInfo:
	def __init__(self):
		self.cmdtype = FSCmdType.FILE_INFO
		self.session_id = None
		self.token = None
		self.path = None
		self.length = None
		self.type = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
			'path' : self.path ,	
			'length' : self.length ,	
			'type' : self.type ,	
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDFileInfo()
		c.token = d.get('token')
		c.path = d.get('path')
		c.length = d.get('length')
		c.type = d.get('type')
		
		return c
	
	@staticmethod
	def from_cmd(cmd):
		p = FSCMDFileInfo()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		p.path = cmd.params[2]
		p.length = cmd.params[3]
		p.type = cmd.params[4]
		return p
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		cmd.params.append(self.path)
		cmd.params.append(self.length)
		cmd.params.append(self.type)
		return cmd.to_bytes()
		
class FSCMDGetFile:
	def __init__(self):
		self.cmdtype = FSCmdType.GET_FILE
		self.session_id = None
		self.token = None
		self.path = None

	@staticmethod
	def from_cmd(cmd):
		p = FSCMDGetFile()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		p.path = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
			'path' : self.path ,	
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDGetFile()
		c.token = d['token']
		c.path = d['path']
		
		return c
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		cmd.params.append(self.path)
		return cmd.to_bytes()

		
class FSCMDFileData:
	def __init__(self):
		self.cmdtype = FSCmdType.FILE_DATA
		self.session_id = None
		self.token = None
		self.total = None
		self.start = None
		self.data = None
		
	@staticmethod
	def from_cmd(cmd):
		p = FSCMDFileData()
		p.session_id = cmd.params[0]
		p.token = cmd.params[1]
		p.total = cmd.params[2]
		p.start = cmd.params[3]
		p.data = cmd.params[3]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
			'total' : self.total ,
			'start' : self.start ,
			'data' : self.data ,
		}
	
	@staticmethod
	def from_dict(d):
		c = FSCMDFileData()
		c.token = d['token']
		c.total = d['total']
		c.start = d['start']
		c.data  = d['data']
		return c
		
	def to_bytes(self):
		cmd = FSPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		cmd.params.append(self.total)
		cmd.params.append(self.start)
		cmd.params.append(self.data)
		return cmd.to_bytes()
		
class FSPluginCMD:
	def __init__(self):
		self.cmdtype = None
		self.params = []
	
	@staticmethod
	def from_string(data):
		return FSPluginCMD.from_bytes(bytes.fromhex(data))
		
	@staticmethod
	def from_bytes(data):
		return FSPluginCMD.from_buffer(io.BytesIO(data))
		
	@staticmethod
	def from_dict(d):
		ct = FSCmdType(d['cmdtype'])
		return type2obj[ct].from_dict(d)
		
		
	@staticmethod
	def from_buffer(buff):
		cmd = FSPluginCMD()
		cmd.cmdtype = FSCmdType(buff.read(1)[0])
		param_len = buff.read(1)[0]
		for _ in range(param_len):
			plen = int.from_bytes(buff.read(4), 'big', signed = False)
			if plen == 0:
				cmd.params.append(None)
				
			cmd.params.append(buff.read(plen).decode())
			
		if cmd.cmdtype in type2obj and type2obj[cmd.cmdtype]:
			return type2obj[cmd.cmdtype].from_cmd(cmd)
		return cmd
		
	def to_bytes(self):
		t = self.cmdtype.value.to_bytes(1, 'big', signed = False)
		t += len(self.params).to_bytes(1, 'big', signed = False)
		for i in range(len(self.params)):
			p = eon(self.params[i])
			#we signal the None parameter as zero length and no value
			if not p:
				t += b'\x00'*4
				continue
			t += len(p).to_bytes(4, 'big', signed = False)
			t += p
		return t
		
	def to_string(self):
		return self.to_bytes().hex()
		
	def __str__(self):
		t = '==== FSPluginCMD ====\r\n'
		t += 'cmdtype: %s\r\n' % self.cmdtype.name
		for i, val in enumerate(self.params):
			t += 'var%s: %s\r\n' % (i, val)
		
		return t

type2obj = {
	FSCmdType.CONNECT : FSCMDConnect, 
	FSCmdType.TERMINATED : FSCMDError, 
	FSCmdType.ERR : FSCMDError,
	FSCmdType.OK : FSCMDOK,
	FSCmdType.LIST : FSCMDList,
	FSCmdType.FILE_INFO : FSCMDFileInfo,
	FSCmdType.GET_FILE : FSCMDGetFile,
	FSCmdType.FILE_DATA : FSCMDFileData,
}