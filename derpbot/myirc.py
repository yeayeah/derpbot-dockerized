import rocksock
import time
import threading
import random

class IRC():
	def __init__(self, server, port, nick, chan, ssl, proxies=None, auth=None):
		self.server = server
		self.port = port
		self.nick = nick
		self.mynick = nick
		self.current_nick = None
		self.chan = chan
		self.auth = auth
		self.ssl = ssl
		self.proxies = proxies
		self.hostname = ''

	def login(self):
		self.socket.send('NICK %s\nUSER %s %s localhost :%s\n' % (self.nick, self.nick, self.server, self.nick))

	def connect(self):
		socket = rocksock.Rocksock(host=self.server,port=self.port,ssl=self.ssl,proxies=self.proxies)
		socket.connect()
		self.socket = socket
		self.login()

	def recvline(self):
		while True:
			try: recv = self.socket.recvline()
			except Exception as e:
				print(e)
				break

			recv = recv.strip()
			parsed = self.parse(recv)
			if parsed is False: return False
			elif parsed is None: continue
			else: return recv
		return False

	def send(self, data, delay=0):
		if delay == 0:
			self.socket.send('%s\n' % data)
		else:
			threading.Timer(delay, self.send, args=(data, 0)).start()

	def join(self, chan, key=None):
		if key: self.socket.send('JOIN %s %s\n' % (chan, key))
		else: self.socket.send('JOIN %S\n' %chan)

	def part(self, chan, reason='leaving'):
		self.socket.send('PART %s :%s\n' % (chan, reason))

	def cycle(self, chan, key=None, reason='cycle'):
		self.part(chan, reason)
		self.join(chan, key)

	def privmsg(self, dest, message):
		avail = 512
		# user!ident@host privmsg #dest :<data>
		avail = avail - ( (len(self.nick)*2) + 2 + len(self.hostname) + len('privmsg') + len(dest) + 4)
		self.socket.send('PRIVMSG %s :%s\n' %(dest, message[:avail]))

	def notice(self, dest, message):
		avail = 512
		# user!ident@host notice #dest :<data>
		avail = avail - ( (len(self.nick)*2) + 2 + len(self.hostname) + len('notice') + len(dest) + 4)
		self.socket.send('NOTICE %s :%s\n' %(dest, message[:avail]))

	def parse(self, recv):
		print('> %s' %recv)
		#if recv.startswith(':%s!' % self.nick): return None
		# clean disconnect
		if recv.startswith('ERROR'): return False
		# ping request
		elif recv.startswith('PING'): self.socket.send( recv.replace('I','O', True) )
		# sasl stuff
		elif recv.find('CAP %s ACK :sasl' %self.nick) != -1:
			self.socket.send('AUTHENTICATE PLAIN\n')
		elif recv.startswith('AUTHENTICATE +'):
			import base64
			username, password = self.auth.split(' ')
			sasl = base64.b64encode("%s\0%s\0%s" % (username, username, password)).decode()
			self.socket.send('AUTHENTICATE %s\nCAP END\n' % sasl.encode('utf-8'))
		# sasl not supported, fallback to nickserv auth
		elif recv.find('CAP %s NAK :sasl' %self.nick) != -1:
			self.socket.send('NICKSERV IDENTIFY %s %s\n' % (self.auth.split(' ')[0], self.auth.split(' ')[1]))
		# ignore other lines not starting with ':'
		elif recv[0] != ':': return None

		else:
			split = recv.split(' ')
			if split[1] == '001': pass
			elif split[1] == '372': return None
			# ping/pong game
			elif split[1] == 'PONG': self.send('PING :%s' %self.nick, 5)

			elif split[1] == 'NICK':
				if split[0].startswith(':%s!' %self.nick):
					self.nick = split[2].lstrip(':')
			# sasl auth success
			elif split[1] == '903':
				self.socket.send('JOIN %s\n' %self.chan)
			elif split[1] == '376':
				# initiate ping/pong game
				self.socket.send('PING :%s\n' % self.nick)
				# initiate sasl auth
				if self.auth is not None: self.socket.send('CAP REQ :sasl\n')
				# or simply join chans
				else:	self.socket.send('JOIN %s\n' %self.chan)
			# someone quits
			elif split[1] == 'QUIT':
				# regain nick?
				if split[0].startswith(':%s!' %self.mynick):
					self.socket.send('NICK %s\n' %self.mynick)
			# nick already used
			elif split[1] == '433':
				self.nick = ''.join(random.sample(self.nick, len(self.nick)))
				self.socket.send('NICK %s\n' %self.nick)
				self.socket.send('WHO %s\n' %self.mynick)
			# WHO reply
			elif split[1] == '352':
				if split[7] == self.mynick and self.nick != self.mynick:
					self.send('WHO %s' %self.mynick, 15)
				elif split[7] == self.nick:
					self.socket.send('NICK %s\n' % self.mynick)

			#:strontium.libera.chat NOTICE * :*** Found your hostname: cgn05-185-6-233-136.internet.lu
			elif split[1] == 'NOTICE':
				if split[0].find('!') == -1:
					message = ' '.join( split[2:] )
					if message.find('Found your hostname:') != -1: self.hostname = split[7]
		return True
