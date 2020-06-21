import asyncio
import websockets
import json
import base64
import multiprocessing

from multiplexor.utils.apq import AsyncProcessQueue
from multiplexor.plugins.sspi.pluginprotocol import *

class KerberosSSPIClient:
	def __init__(self, url):
		self.server_url = url
		self.transport = None
		
	async def connect(self):
		self.transport = await websockets.connect(self.server_url)
	
	async def disconnect(self):
		ac = SSPITerminateCmd()
		await self.transport.send(json.dumps(ac.to_dict()))
		self.transport.close()

	async def authenticate(self, target_name, flags = None, token_data = None):
		try:
			ac = SSPIKerberosAuthCmd()
			ac.client_name = None
			ac.cred_usage = '3'
			ac.flags = flags
			ac.target_name = target_name

			ac.token_data = token_data
			if token_data is not None:
				ac.token_data = base64.b64encode(token_data).decode()
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			if rply.cmdtype == SSPICmdType.Winerror:
				return None, rply.get_exception()
			return base64.b64decode(rply.authdata), None
		except Exception as e:
			return None, e

	async def get_session_key(self):
		try:
			ac = SSPIGetSessionKeyCmd()
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			return base64.b64decode(rply.session_key), None
		except Exception as e:
			return None, e

	async def get_seq_number(self):
		try:
			ac = SSPIGetSequenceNoCmd()
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			return base64.b64decode(rply.seq_number), None
		except Exception as e:
			return None, e

class SSPINTLMClient:
	def __init__(self, url):
		self.server_url = url
		self.transport = None
		
	async def connect(self):
		self.transport = await websockets.connect(self.server_url)

	async def disconnect(self):
		ac = SSPITerminateCmd()
		await self.transport.send(json.dumps(ac.to_dict()))
		self.transport.close()
		
	async def authenticate(self, flags = None):
		try:
			ac = SSPINTLMAuthCmd()
			ac.client_name = None
			ac.cred_usage = '3'
			if flags is not None:
				ac.flags = str(flags)
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			if rply.cmdtype == SSPICmdType.Winerror:
				return None, rply.get_exception()
				
			return base64.b64decode(rply.authdata), None
		except Exception as e:
			return None, e
		
	async def challenge(self, challenge, flags = None):
		try:
			ac = SSPINTLMChallengeCmd()
			ac.cred_usage = '3'
			if flags is not None:
				ac.flags = str(flags)
			ac.token = base64.b64encode(challenge).decode()
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			if rply.cmdtype == SSPICmdType.Winerror:
				return None, rply.get_exception()
			return base64.b64decode(rply.authdata), None
		
		except Exception as e:
			return None, e

	async def get_session_key(self):
		try:
			ac = SSPIGetSessionKeyCmd()
			await self.transport.send(json.dumps(ac.to_dict()))
			data = await self.transport.recv()
			rply = SSPIPluginCMD.from_dict(json.loads(data))
			if rply.cmdtype == SSPICmdType.Winerror:
				return None, rply.get_exception()
			return base64.b64decode(rply.session_key), None
		except Exception as e:
			return None, e
		
		
class LDAP3NTLMSSPIProcess(multiprocessing.Process):
	def __init__(self, url, in_q, out_q):
		multiprocessing.Process.__init__(self)
		self.client = None
		self.in_q = in_q
		self.out_q = out_q
		self.url = url

	async def main(self):
		self.client = SSPINTLMClient(self.url)
		await self.client.connect()
		data, res = await self.client.authenticate()
		await self.out_q.coro_put((data, res))
		autorize_data = await self.in_q.coro_get()
		data, res = await self.client.challenge(autorize_data)
		await self.out_q.coro_put((data, res))

	def run(self):
		asyncio.run(self.main())

class LDAP3NTLMSSPI:
	def __init__(self, user_name = None, domain = None, password = None):
		##
		## Since this is a monkey patching object, we cannot control the input parameter count
		## We need to know the URL tho, and since the password filed is not used norally (no point using this object if you know the password)
		## The password filed is used to get the actual URL of the SSPI server
		##
		## Make no mistake, this "solution" is as ugly as it gets. The reason I use this is: I really don't wish to re-write the enitre ldap3 library...
		##
		
		
		self.client_name = None
		self.target_name = None
		self.password = password
		
		self.authenticate_data = None
		self.aproc = None
		self.in_q = AsyncProcessQueue()
		self.out_q = AsyncProcessQueue()
		
	def create_negotiate_message(self):
		#print('Connecting to %s' % self.password)
		self.aproc = LDAP3NTLMSSPIProcess(self.password, self.in_q, self.out_q)
		self.aproc.start()
		#print('Connected!')
		#print('Getting auth data!')
		data, res = self.out_q.get()

		return data
		
	def create_authenticate_message(self):
		return self.authenticate_data
		
	def parse_challenge_message(self, autorize_data):
		#print('Getting authenticate data!')
		self.in_q.put(autorize_data)
		data, res = self.out_q.get()
		self.authenticate_data = data
	