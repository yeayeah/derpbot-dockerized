import rocksock
import time
import threading
import random
import misc
import users

class IRC():
	def __init__(self, server, port, nick, chan, ssl, proxies=None, auth=None, oper=None, silence=None):
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
		self.authed = False
		self.oper = oper
		self.silence = silence
		self.nicklist = dict()

	def login(self):
		self.socket.send('NICK %s\nUSER %s %s localhost :%s\n' % (self.nick, self.nick, self.server, self.nick))

	def identify(self, method):
		if not self.auth or self.authed: return
		elif method == 'nickserv':
			self.send('NICKSERV IDENTIFY %s' % self.auth)
		elif method == 'b64':
			import base64
			username, password = self.auth.split(' ')
			sasl = base64.b64encode("%s\0%s\0%s" % (username, username, password)).decode()
			self.send('AUTHENTICATE %s\nCAP END' % sasl.encode('utf-8'))
		elif method == 'auth':
			self.send('AUTH %s' % self.auth.replace(' ', ':', True))

		self.authed = True

	def connect(self):
		socket = rocksock.Rocksock(host=self.server,port=self.port,ssl=self.ssl,proxies=self.proxies)
		try: socket.connect()
		except: return False
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

	def privmsg(self, dest, message, delay=0):
		avail = 512
		# user!ident@host privmsg #dest :<data>
		avail = avail - ( (len(self.nick)*2) + 2 + len(self.hostname) + len('privmsg') + len(dest) + 4)
		if delay == 0: self.socket.send('PRIVMSG %s :%s\n' %(dest, message[:avail]))
		else: threading.Timer(delay, self.privmsg, (dest, message, 0)).start()

	def notice(self, dest, message, delay=0):
		avail = 512
		# user!ident@host notice #dest :<data>
		avail = avail - ( (len(self.nick)*2) + 2 + len(self.hostname) + len('notice') + len(dest) + 4)
		if delay == 0: self.socket.send('NOTICE %s :%s\n' %(dest, message[:avail]))
		else: threading.Timer(delay, self.notice, (dest, message, 0)).start()

	def _build_nicklist(self, chan, nicks):
		if not chan in self.nicklist: self.nicklist[chan] = dict()
		modes = {'@': 'op', '%': 'halfop', '+': 'voice'}
		for nick in nicks:
			_dict = dict()
			for mode in modes:
				if nick.find(mode) != -1:
					nick = nick.replace( mode, '', True)
					_dict[ modes[mode] ] = True

			self.nicklist[chan][nick] = _dict

	def parse(self, recv):
		print('> %s' %repr(recv))
		#if recv.startswith(':%s!' % self.nick): return None
		# clean disconnect
		if recv.startswith('ERROR'): return False
		# ping request
		elif recv.startswith('PING'):
			self.send( recv.replace('I','O', True) )
		# sasl stuff
		elif recv.find('CAP %s ACK :sasl' %self.nick) != -1:
			self.socket.send('AUTHENTICATE PLAIN\n')
		elif recv.startswith('AUTHENTICATE +'):
			self.identify(method='b64')
		# sasl not supported, fallback to nickserv auth
		elif recv.find('CAP %s NAK :sasl' %self.nick) != -1:
			self.identify(method='nickserv')
		# ignore lines not starting with ':'
		elif recv[0] != ':': return None

		split = recv.split(' ')
		if split[1] == '372': return None
		elif split[1] == 'PONG': self.send('PING :%s' %self.nick, 5)
		elif split[1] == '001':
			if self.oper is not None: self.socket.send('OPER %s\n' % self.oper)
			if self.silence and 'SILENCE' in self.servermode.keys():
				_ = [ self.socket.send('SILENCE %s' %silence.strip()) for silence in self.silence.split(',') if time.sleep(0.3) ]
			# initiate sasl auth
			if self.auth: self.socket.send('CAP REQ :sasl\n')
		# server modes
		elif split[1] == '005':
			if not hasattr(self, 'servermode'): self.servermode = dict()
			for i in split[3:]:
				if i[0] == ':': break
				elif i.find('=') != -1: item, value = i.split('=')
				else: item, value = [i, 1]
				self.servermode[item] = value
			return None
		# WHO reply
		elif split[1] == '352':
			if split[7] == self.mynick and self.nick != self.mynick:
				self.send('WHO %s' %self.mynick, 15)
			elif split[7] == self.nick:
				self.socket.send('NICK %s\n' % self.mynick)
		# getting nicklist
		elif split[1] == '353':
			chan = split[4]
			nicks = [ n for n in ' '.join( split[5:]).lstrip(':').split(' ') ]
			self._build_nicklist(chan=chan, nicks=nicks)
		# nick already used
		elif split[1] == '433':
			self.nick = ''.join(random.sample(self.nick, len(self.nick)))
			self.socket.send('NICK %s\n' %self.nick)
			self.socket.send('WHO %s\n' %self.mynick)

		# sasl auth success
		elif split[1] == '900':
			self.authed = True
			_, self.hostname = split[3].split('@')
		elif split[1] == '903':
			if self.chan: self.socket.send('JOIN %s\n' %self.chan)

		elif split[1] == 'INVITE':
			user, mask = misc.nickmask(split[0])
			if users.get_user_access(self, mask) <= 5:
				self.send('JOIN %s' %split[3].lstrip(':'))

		# /MOTD, or MOTD missing
		elif split[1] == '376' or split[1] == '422':
			# initiate ping/pong game
			self.socket.send('PING :%s\n' % self.nick)
			# join chans
			if self.chan and (self.auth and self.authed) or not self.auth: self.socket.send('JOIN %s\n' %self.chan)

		elif split[1] == 'NICK':
			nick = split[0][1:]
			#if split[0].startswith(':%s!' %self.nick):
			if nick == self.nick:
				self.nick = split[2].lstrip(':')
			else:
				newnick = split[2][1:]
				for chan in self.nicklist:
					if chan[0] == '#':
						if not nick in self.nicklist[chan]: continue
						self.nicklist[chan][newnick] = self.nicklist[chan].pop(nick)

		elif split[1] == 'NOTICE':
			if split[0].find('!') == -1:
				message = ' '.join( split[2:] )
				if message.find('Found your hostname:') != -1:
					self.hostname = split[7]
				elif message.find('QUOTE AUTH') != -1:
					self.identify(method='auth')

		elif split[1] == 'JOIN':
			chan = split[2].lstrip(':')
			nick, mask = misc.nickmask(split[0])
			if split[0].startswith(':%s!' % self.nick): self.nicklist[chan] = dict()
			else: self.nicklist[chan][nick] = dict()

		elif split[1] == 'PART':
			chan = split[2].lstrip(':')
			nick, mask = misc.nickmask(split[0])
			del( self.nicklist[chan][nick] )

		# someone quits
		elif split[1] == 'QUIT':
			nick, mask = misc.nickmask(split[0])
			# regain nick?
			if nick == self.mynick:
				self.socket.send('NICK %s\n' %self.mynick)
			for chan in self.nicklist:
				if chan[0] == '#':
					if nick in self.nicklist[chan]: del( self.nicklist[chan][nick] )

		elif split[1] == 'KICK':
			chan = split[2].lstrip(':')
			kicked = split[3]
			if kicked == self.nick: del( self.nicklist[chan] )
			else: del( self.nicklist[chan][kicked] )

		return True
