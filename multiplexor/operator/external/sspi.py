import asyncio
import websockets
import json
import base64
import multiprocessing

from multiplexor.utils.apq import AsyncProcessQueue
from multiplexor.plugins.sspi.pluginprotocol import *

class SSPINTLMClient:
	def __init__(self, url):
		self.server_url = url
		self.transport = None
		self.data = None
		
	async def connect(self):
		self.transport = await websockets.connect(self.server_url)
		
	async def authenticate(self):
		ac = SSPINTLMAuthCmd()
		ac.client_name = None
		ac.cred_usage = '3'
		await self.transport.send(json.dumps(ac.to_dict()))
		data = await self.transport.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		self.data = rply.authdata
		
	async def challenge(self, challenge):
		ac = SSPINTLMChallengeCmd()
		ac.cred_usage = '3'
		ac.token = base64.b64encode(challenge).decode()
		await self.transport.send(json.dumps(ac.to_dict()))
		data = await self.transport.recv()
		rply = SSPIPluginCMD.from_dict(json.loads(data))
		self.data = rply.authdata
		
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
		await self.client.authenticate()
		await self.out_q.coro_put(self.client.data)
		autorize_data = await self.in_q.coro_get()
		await self.client.challenge(autorize_data)
		await self.out_q.coro_put(self.client.data)

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
		print('Connecting to %s' % self.password)
		self.aproc = LDAP3NTLMSSPIProcess(self.password, self.in_q, self.out_q)
		self.aproc.start()
		print('Connected!')
		print('Getting auth data!')
		data = self.out_q.get()

		return base64.b64decode(data)
		
	def create_authenticate_message(self):
		return self.authenticate_data
		
	def parse_challenge_message(self, autorize_data):
		print('Getting authenticate data!')
		self.in_q.put(autorize_data)
		data = self.out_q.get()
		self.authenticate_data = base64.b64decode(data)
	