import enum
import io

"""
All command parameters are sent as string or None
"""

class SSPICmdType(enum.Enum):
	CONNECT = 0
	TERMINATED = 1
	NTLM_AUTH = 2
	NTLM_AUTH_RPLY = 3
	NTLM_CHALLENGE = 4
	NTLM_CHALLENGE_RPLY = 5
	KERBEROS_AUTH = 6
	KERBEROS_AUTH_RPLY = 7
	DecryptMessage = 8
	DecryptMessageRply = 9
	EncryptMessage = 10
	EncryptMessageRply = 11	
	Winerror = 12
	
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
	
class WinError:
	def __init__(self):
		self.cmdtype = SSPICmdType.Winerror
		self.session_id = None
		self.result = None
		self.reason = None

	@staticmethod
	def from_cmd(cmd):
		p = WinError()
		p.session_id = cmd.params[0]
		p.result = cmd.params[1]
		p.reason = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'result' : self.result ,
			'reason' : self.reason ,	
		}
		
	def from_dict(d):
		c = WinError()
		c.result = d['result']
		c.reason = d['reason']
		
		return c
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.result)
		cmd.params.append(self.reason)
		return cmd.to_bytes()
		
class SSPIConnectCmd:
	def __init__(self):
		self.cmdtype = SSPICmdType.CONNECT
		self.session_id = None
	
	@staticmethod
	def from_cmd(cmd):
		p = SSPIConnectCmd()
		p.session_id = cmd.params[0]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		return cmd.to_bytes()
		
class SSPINTLMAuthCmd:
	def __init__(self):
		self.cmdtype = SSPICmdType.NTLM_AUTH
		self.session_id = None
		self.client_name = None
		self.cred_usage = None
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'client_name' : self.client_name ,
			'cred_usage' : self.cred_usage ,	
		}
		
	def from_dict(d):
		c = SSPINTLMAuthCmd()
		c.client_name = d['client_name']
		c.cred_usage = d['cred_usage']
		
		return c
	
	@staticmethod
	def from_cmd(cmd):
		p = SSPINTLMAuthCmd()
		p.session_id = cmd.params[0]
		p.client_name = cmd.params[1]
		p.cred_usage = cmd.params[2]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.client_name)
		cmd.params.append(self.cred_usage)
		return cmd.to_bytes()
		
class SSPINTLMAuthRply:
	def __init__(self):
		self.cmdtype = SSPICmdType.NTLM_AUTH_RPLY
		self.session_id = None
		self.result = None
		self.authdata = None

	@staticmethod
	def from_cmd(cmd):
		p = SSPINTLMAuthRply()
		p.session_id = cmd.params[0]
		p.result = cmd.params[1]
		p.authdata = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'result' : self.result ,
			'authdata' : self.authdata ,	
		}
		
	def from_dict(d):
		c = SSPINTLMAuthRply()
		c.result = d['result']
		c.authdata = d['authdata']
		
		return c
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.result)
		cmd.params.append(self.authdata)
		return cmd.to_bytes()
		
class SSPINTLMChallengeCmd:
	def __init__(self):
		self.cmdtype = SSPICmdType.NTLM_CHALLENGE
		self.session_id = None
		self.token = None
		
	@staticmethod
	def from_cmd(cmd):
		p = SSPINTLMChallengeCmd()
		p.session_id = cmd.params[0]
		p.authdata = cmd.params[1]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'token' : self.token ,
		}
		
	def from_dict(d):
		c = SSPINTLMChallengeCmd()
		c.token = d['token']
		return c
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.token)
		return cmd.to_bytes()
		

class SSPINTLMChallengeRply:
	def __init__(self):
		self.cmdtype = SSPICmdType.NTLM_CHALLENGE_RPLY
		self.session_id = None
		self.result = None
		self.authdata = None

	@staticmethod
	def from_cmd(cmd):
		p = SSPINTLMChallengeRply()
		p.session_id = cmd.params[0]
		p.result = cmd.params[1]
		p.authdata = cmd.params[2]
		return p
		
	def to_dict(self):
		return {
			'cmdtype' : self.cmdtype.value,
			'result' : self.result ,
			'authdata' : self.authdata ,	
		}
		
	def from_dict(d):
		c = SSPINTLMChallengeRply()
		c.result = d['result']
		c.authdata = d['authdata']
		
		return c
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.result)
		cmd.params.append(self.authdata)
		return cmd.to_bytes()
		
class SSPIInitializeSecurityContextCmd:
	def __init__(self):
		self.cmdtype = SSPICmdType.InitializeSecurityContext
		self.session_id = None
		self.creds = None
		self.target = None
		self.ctx  = None
		self.flags  = None
		self.TargetDataRep  = None
		self.token  = None
	
	@staticmethod
	def from_cmd(cmd):
		p = SSPIAcquireCredentialsHandleCmd()
		p.session_id = cmd.params[0]
		p.creds = cmd.params[1]
		p.target = cmd.params[2]
		p.ctx = cmd.params[3]
		p.flags = cmd.params[4]
		p.TargetDataRep = cmd.params[5]
		p.token = cmd.params[6]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.creds)
		cmd.params.append(self.target)
		cmd.params.append(self.ctx)
		cmd.params.append(self.flags)
		cmd.params.append(self.TargetDataRep)
		cmd.params.append(self.token)
		return cmd.to_bytes()
		
class SSPIInitializeSecurityContextRply:
	def __init__(self):
		self.cmdtype = SSPICmdType.InitializeSecurityContextRply
		self.session_id = None
		self.res = None
		self.ctx = None
		self.data  = None
		self.outputflags  = None
		self.expiry  = None
	
	@staticmethod
	def from_cmd(cmd):
		p = SSPIInitializeSecurityContextRply()
		p.session_id = cmd.params[0]
		p.res = cmd.params[1]
		p.ctx = cmd.params[2]
		p.data = cmd.params[3]
		p.flags = cmd.params[4]
		p.outputflags = cmd.params[5]
		p.expiry = cmd.params[6]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.res)
		cmd.params.append(self.ctx)
		cmd.params.append(self.data)
		cmd.params.append(self.flags)
		cmd.params.append(self.outputflags)
		cmd.params.append(self.expiry)
		return cmd.to_bytes()
		
class SSPIDecryptMessageCmd:
	def __init__(self):
		self.cmdtype = SSPICmdType.DecryptMessage
		self.session_id = None
		self.ctx = None
		self.data = None
		self.message_no = None

	@staticmethod
	def from_cmd(cmd):
		p = SSPIDecryptMessageCmd()
		p.session_id = cmd.params[0]
		p.ctx = cmd.params[1]
		p.data = cmd.params[2]
		p.message_no = cmd.params[3]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.ctx)
		cmd.params.append(self.data)
		cmd.params.append(self.message_no)
		return cmd.to_bytes()
		
class SSPIDecryptMessageRply:
	def __init__(self):
		self.cmdtype = SSPICmdType.DecryptMessageRply
		self.session_id = None
		self.data = None

	@staticmethod
	def from_cmd(cmd):
		p = SSPIDecryptMessageRply()
		p.session_id = cmd.params[0]
		p.data = cmd.params[1]
		return p
		
	def to_bytes(self):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = self.cmdtype
		cmd.params.append(self.session_id)
		cmd.params.append(self.data)
		return cmd.to_bytes()
	
class SSPIPluginCMD:
	def __init__(self):
		self.cmdtype = None
		self.params = []
	
	@staticmethod
	def from_string(data):
		return SSPIPluginCMD.from_bytes(bytes.fromhex(data))
		
	@staticmethod
	def from_bytes(data):
		return SSPIPluginCMD.from_buffer(io.BytesIO(data))
		
	@staticmethod
	def from_dict(d):
		ct = SSPICmdType(d['cmdtype'])
		return type2obj[ct].from_dict(d)
		
		
	@staticmethod
	def from_buffer(buff):
		cmd = SSPIPluginCMD()
		cmd.cmdtype = SSPICmdType(buff.read(1)[0])
		param_len = buff.read(1)[0]
		for i in range(param_len):
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
		t = '==== SSPIPluginCMD ====\r\n'
		t += 'cmdtype: %s\r\n' % self.cmdtype.name
		for i, val in enumerate(self.params):
			t += 'var%s: %s\r\n' % (i, val)
		
		return t

type2obj = {
	
	SSPICmdType.CONNECT : SSPIConnectCmd, 
	SSPICmdType.TERMINATED : None, 
	SSPICmdType.NTLM_AUTH : SSPINTLMAuthCmd, 
	SSPICmdType.NTLM_AUTH_RPLY : SSPINTLMAuthRply,
	SSPICmdType.NTLM_CHALLENGE : SSPINTLMChallengeCmd,
	SSPICmdType.NTLM_CHALLENGE_RPLY : SSPINTLMChallengeRply,
	SSPICmdType.KERBEROS_AUTH : None,
	SSPICmdType.KERBEROS_AUTH_RPLY : None,
	SSPICmdType.DecryptMessage : None,
	SSPICmdType.DecryptMessageRply : None,
	SSPICmdType.EncryptMessage : None,
	SSPICmdType.EncryptMessageRply : None,	
	SSPICmdType.Winerror : WinError
	
}