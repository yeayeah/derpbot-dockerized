#!/usr/bin/env python

import myirc
import threading
import rocksock
import plugins
import argparse
import os
import random
import string
import hecketer
import misc
import time
import users

class Derpbot():
	def __init__(self, server, port, nick, chan, triggerchar='!', ssl=False, auth=None, args=None):
		self.server = server
		self.args = args
		self.port = port
		self.nick = nick
		self.mynick = nick
		self.chan = chan
		self.irc = None
		self.ssl = ssl
		self.auth = auth
		self.args.irc_proxy = [ rocksock.RocksockProxyFromURL(i.strip()) for i in args.irc_proxy.split(';') ] if args.irc_proxy else None
		self.args.http_proxy = [ rocksock.RocksockProxyFromURL(i.strip()) for i in args.http_proxy.split(';') ] if args.http_proxy else None
		self.triggerchar = triggerchar
		self.datadir = 'data/%s' %self.server
		self.running = True
		self.threads = []
		self.ownerkey = None
		self.pm = plugins.PluginManager('./plugins') if os.path.isdir('./plugins') else None
		self.hecketer = hecketer.Hecketer(learn=True, proxies=self.args.http_proxy)
		self.nicklist = dict()
		#self.events = { '001': [], 'JOIN': [], 'PRIVMSG': [], 'NOTICE': [], 'INVITE': [] }

	def _settings_load(self):
		fp = os.path.join(self.datadir, 'settings.json')
		self.settings = json.load(fp) if os.path.exists(fp) else dict()

	def _settings_save(self):
		return
		with open(os.path.join( self.datadir, 'settings.json' ), 'w') as h:
			json.dump(self.settings, h, indent=4)

	def run(self):
		if self.pm is not None: self.load_plugins()
		else: self.pmlist = dict()

		self._settings_load()
		self.irc = myirc.IRC(self.server, self.port, self.nick, self.chan, self.ssl, self.args.irc_proxy, self.auth)

		while self.running:
			self._run()

		_settings_save()

	def _loop_events(self, split, recv):

		for p in self.pmlist:
			threading.Timer(0, self.pm.execute_event_hook, (p, {'event': split[1], 'recv': recv, 'self': self })).start()

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

	def is_new_owner(self, split):
		key = split[3][1:]
		if key == self.ownerkey:
			if not os.path.exists('%s/access' %self.datadir):
				with open('%s/access' %self.datadir, 'w') as h:
					h.write('%s 0\n' %mask)
				self.irc.privmsg(nick, 'Hello, master. (%s)' %mask)
				self.ownerkey = None
	def _run(self):
		self.irc.authed = False
		if self.irc.connect() is False: return
		while self.running:
			recv = self.irc.recvline()
			if recv is False: break
			split = recv.split(' ')

			foo = self._loop_events(split, recv)

			# bot command ?
			if split[1] == 'PRIVMSG':
				chan = split[2]
				nick, mask = misc.nickmask(split[0])

				line = split[3:]
				linestr = ' '.join(line)

				if misc.is_ignored_nick(self, nick) or misc.is_ignored_string(self, chan, linestr):
					continue

				if chan == self.irc.nick:
					if self.ownerkey is not None: self.is_new_owner(split)
					continue

				# line starts with bot's name
				if line[0].startswith(':%s' %self.irc.nick):
					command = line[1]
					args = line[2:] if len(line) > 2 else []
					bottalk = True
				# line starts with !command
				elif line[0].startswith(':%s' %self.triggerchar):
					# ignore if we are not the main bot
					if self.irc.mynick != self.irc.nick: continue
					command = line[0][1:].strip( self.triggerchar )
					args = line[1:] if len(line) > 1 else []
					bottalk = False
				# nothing for the bot
				else: continue

				# check if plugin needs to be run
				matches = {}
				if command.find(':') != -1:
					try:
						plugin, command = command.split(':')
						if not plugin in self.pmlist.keys(): continue
						res = self.run_plugin(nick, chan, mask, plugin, command, args)
						if res is not None:
							if 'reply' in res and res['reply']: self.irc.privmsg(chan, res['reply'])
							if 'self' in res and res['self']: self = res['self']
					except: pass
					continue

				for p in self.pmlist.keys():
					m = [ i for i in self.pmlist[p] if i.startswith(command) ]
					if len(m): matches[p] = m

				if len(matches.keys()) == 1 and len(matches[ matches.keys()[0] ]) == 1:
					res = self.run_plugin( nick, chan, mask, matches.keys()[0], matches[matches.keys()[0]][0], args)
					if res is not None:
						if 'reply' in res and res['reply']: self.irc.privmsg(chan, res['reply'])
						if 'self' in res and res['self'] is not None: self = res['self']

				elif len(matches.keys()) > 1:
					self.irc.privmsg(chan, '%s: Ambiguous command. "%s" offer command %s' % (nick, ', '.join( matches.keys()), command))
					self.irc.privmsg(chan, '%s: Use "pluginName:command" if multiple plugins offer the same command.' % nick)
					
				# user wants to talk ?
				elif bottalk:
					reply = self.hecketer.ask(' '.join( line[1:] ))
					if reply is not None:
						self.irc.privmsg(chan, '%s: %s' % (nick, reply))

			elif split[1] == '001':
				if not os.path.exists('%s/access' %self.datadir):
					self.ownerkey = ''.join( random.sample( string.letters, 10 ))
					print('No access file available. Use `/msg %s %s` to auth to the bot' % (self.irc.nick, self.ownerkey) )
			elif split[1] == '376':
				if self.args.silence is not None:
					if 'SILENCE' in self.irc.servermode.keys():
						for silence in self.args.silence.split(';'):
							self.irc.send('SILENCE %s' %silence.strip())
							time.sleep(0.3)

			elif split[1] == 'INVITE':
				user, mask = misc.nickmask(split[0])
				if users.get_user_access(self, mask) > 5: continue
				self.irc.send('JOIN %s' %split[3].lstrip(':'))

			elif split[1] == 'JOIN':
				chan = split[2].lstrip(':')
				nick, mask = misc.nickmask(split[0])
				if split[0].startswith(':%s!' % self.irc.nick): self.nicklist[chan] = dict()
				else: self.nicklist[chan][nick] = dict()

			elif split[1] == 'PART':
				chan = split[2].lstrip(':')
				nick, mask = misc.nickmask(split[0])
				del( self.nicklist[chan][nick] )

			elif split[1] == 'QUIT':
				nick, mask = misc.nickmask(split[0])
				for chan in self.nicklist:
					if chan[0] == '#':
						if nick in self.nicklist[chan]: del( self.nicklist[chan][nick] )

			elif split[1] == 'KICK':
				chan = split[2].lstrip(':')
				kicked = split[3]
				if kicked == self.irc.nick: del( self.nicklist[chan] )
				else: del( self.nicklist[chan][kicked] )

			elif split[1] == 'NICK':
				nick, mask = misc.nickmask(split[0])
				newnick = split[2]
				for chan in self.nicklist:
					if chan[0] == '#':
						if not nick in self.nicklist[chan]: continue
						self.nicklist[chan][newnick] = self.nicklist[chan].pop(nick)

			# getting nicklist
			elif split[1] == '353':
				chan = split[4]
				nicks = [ n for n in ' '.join( split[5:]).lstrip(':').split(' ') ]
				self._build_nicklist(chan=chan, nicks=nicks)


	def load_plugins(self):
		self.pmlist = dict()
		for plugin in self.pm.get_available_plugins():
			self.pm.load_plugin(plugin)
			try: provides = self.pm.execute_action_hook(plugin, { 'command': 'provides' })
			except: provides = [ plugin ]
			finally: self.pmlist[plugin] = provides

	def stop(self):
		if self.irc and self.irc.nick == self.irc.mynick: self._settings_save()
		threads = [ t for t in self.threads if t.is_alive() ]
		for t in threads: t.join()
		if self.irc:
			try: self.irc.send('QUIT :leaving')
			except Exception as e: print(repr(e))
		self.running = False
		self.connected = False

	def run_plugin(self, nick, chan, mask, plugin, command, args):
		try: res = self.pm.execute_action_hook(plugin, {
			'command': command,
			'args': args,
			'self': self,
			'nick': nick,
			'mask': mask,
			'chan': chan 
		})
		except Exception as e:
			print('cannot exec plugin "%s" because of: %s' % (plugin, e))
			res = None
		finally:
			return res

if __name__ == '__main__':
	if not os.path.exists('plugins/plugin'): os.popen('cp -r plugins-default/* plugins/')
	parser = argparse.ArgumentParser()
	parser.add_argument('--dockerized', help="indicates it's run through docker.  Will fetch nick, server, ... over env. variables. (default: True)", type=bool, default=True, required=False)
	parser.add_argument('--nick', help="nickname to use", type=str, default='derpbot', required=False)
	parser.add_argument('--chan', help="#some,#chan,#to,#join", type=str, default='##derpbot', required=False)
	parser.add_argument('--server', help="irc server to connect", type=str, default="irc.libera.chat", required=False)
	parser.add_argument('--port', help="port to connect to", type=int, default=6697, required=False)
	parser.add_argument('--use-ssl', help="use ssl? (default: true)", type=bool, default=True, required=False)
	parser.add_argument('--auth', help="define username/password to identify to. format 'username password'", type=str, default=None, required=False)
	parser.add_argument('--irc_proxy', help="proxy/ies to use/chain for IRC connections. Format: sock4://127.0.0.1:9050,http://1.2.3.4:8080,...", type=str, default=None, required=False)
	parser.add_argument('--http_proxy', help="proxy/ies to use/chain for HTTP(s) connections. Format: sock4://127.0.0.1:9050,http://1.2.3.4:8080,...", type=str, default=None, required=False)
	parser.add_argument('--silence', help="user;separated;list of nicknames to ignore globally", type=str, default=None, required=False)
	parser.add_argument('--triggerchar', help="trigger char (default: !)", type=str, default='!', required=False)

	args = parser.parse_args()

	if args.dockerized:
		args.nick = os.getenv('NICK', 'derpyderp')
		args.server = os.getenv('SERVER', 'irc.libera.chat')
		args.port = int( os.getenv('PORT', 6697) )
		args.chan = os.getenv('CHAN', '##derpbot')
		args.auth = os.getenv('AUTH', None)
		args.use_ssl = bool(os.getenv('SSL', 1))
		args.irc_proxy = os.getenv('IRC_PROXY', None)
		args.http_proxy = os.getenv('HTTP_PROXY', None)
		args.triggerchar = os.getenv('TRIGGERCHAR', '!')
		args.silence = os.getenv('SILENCE', None)

	if not os.path.exists('data/%s' %args.server):
		try:
			os.makedirs('data/%s' %args.server)
		except Exception as e:
			print('ERROR: cannot create "data/%s" directory' %args.server)
			raise

	derp = Derpbot(server=args.server, port=args.port, nick=args.nick, chan=args.chan, ssl=args.use_ssl, auth=args.auth, triggerchar=args.triggerchar, args=args)

	try: derp.run()
	except KeyboardInterrupt: pass
	except: raise
	finally: derp.stop()
