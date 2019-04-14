import asyncio
import websockets
import json
import base64

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
		
		
class LDAP3NTLMSSPI:
	def __init__(self, user_name = None, domain = None, password = None):
		url = 'ws://127.0.0.1:58232'
		self.client = SSPINTLMClient(url)
		
		self.client_name = None
		self.target_name = None
		
		self.authenticate_data = None
		
	def create_negotiate_message(self):
		print('Connecting to %s' % self.client.server_url)
		asyncio.get_event_loop().run_until_complete(self.client.connect())
		print('Connected!')
		print('Getting auth data!')
		asyncio.get_event_loop().run_until_complete(self.client.authenticate())
		
		return base64.b64decode(self.client.data)
		
	def create_authenticate_message(self):
		return self.authenticate_data
		
		
	def parse_challenge_message(self, autorize_data):
		print('Getting authenticate data!')
		asyncio.get_event_loop().run_until_complete(self.client.challenge(autorize_data))
		self.authenticate_data = base64.b64decode(self.client.data)
	