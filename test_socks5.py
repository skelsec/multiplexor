import sys
from multiplexor.plugins.socks5.socks5protocol import *

async def socks5test(target_ip, target_port):
	try:
		address = 'google.com'
		port = 80
		print('Connecting to %s:%s' % (target_ip, target_port))
		reader, writer = await asyncio.open_connection(target_ip, target_port)
		print('Connected!')
		nego = SOCKS5Nego.construct(SOCKS5Method.NOAUTH)
		writer.write(nego.to_bytes())
		
		nr = await SOCKS5NegoReply.from_streamreader(reader)
		print(str(nr))
		req = SOCKS5Request.construct(SOCKS5Command.CONNECT, address, port)
		writer.write(req.to_bytes())
		
		rep = await SOCKS5Reply.from_streamreader(reader)
		print(rep)
		await asyncio.sleep(1)
		request = b'GET / HTTP/1.1\r\nHost: google.com\r\n\r\n'
		writer.write(request)
		data = await reader.read(1024)
		print(data)
	
	except Exception as e:
		print(e)


if __name__ == '__main__':
	target_ip = '127.0.0.1'
	target_port = int(sys.argv[1])
	
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(socks5test(target_ip, target_port))
	loop.close()
	
	
	