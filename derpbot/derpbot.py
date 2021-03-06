#!/usr/bin/env python

import json
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

	def _settings_load(self):
		fp = os.path.join(self.datadir, 'settings.json')
		self.settings = json.load(fp) if os.path.exists(fp) else dict()
		fp = os.path.join(self.datadir, 'users.json')
		if os.path.exists(fp):
			with open(fp, 'r') as h: self.users = json.load(h)
		else: self.users = dict()

	def _settings_save(self):
		if hasattr(self, 'users') and len(self.users):
			with open(os.path.join( self.datadir, 'users.json'), 'w') as h:
				json.dump(self.users, h, indent=4)
		return
		if hasattr(self, 'settings'):
			with open(os.path.join( self.datadir, 'settings.json' ), 'w') as h:
				json.dump(self.settings, h, indent=4)


	def run(self):
		if self.pm is not None: self.load_plugins()
		else: self.pmlist = dict()

		self.irc = myirc.IRC(self.server, self.port, self.nick, self.chan, self.ssl, self.args.irc_proxy, self.auth, oper=self.args.oper, silence=self.args.silence)

		while self.running:
			self._settings_load()
			self._run()
			self._settings_save()

	def _loop_events(self, split, recv):
		for p in self.pmlist:
			provides = self.pm.execute_event_hook(p, {'command': 'provides'})
			if provides and split[1] in provides:
				threading.Timer(0, self.pm.execute_event_hook, (p, {'event': split[1], 'recv': recv, 'self': self, 'command': None })).start()

	def parse_privmsg(self, recv, split, chan, nick, mask, line):
		command, args, self.bottalk = self.extract_command(line)
		matches = self.get_matching_commands(command)
		if len(matches.keys()) == 1 and len(matches[ matches.keys()[0] ]) == 1:
			res = self.run_plugin( nick, chan, mask, matches.keys()[0], matches[matches.keys()[0]][0], args)
			if res is not None:
				if 'self' in res and res['self'] is not None: self = res['self']
				if 'reply' in res and res['reply']: self.irc.privmsg(chan, res['reply'])
		elif len(matches.keys()) > 1:
			self.irc.privmsg(chan, '%s: Ambiguous command. Plugins `%s` offer trigger `%s`' % (nick, '`, `'.join( matches.keys()), command))
			self.irc.privmsg(chan, '%s: Use `pluginName:trigger` if multiple plugins offer the same trigger.' % nick)
		elif self.bottalk:
			threading.Timer(0, self.hecketer.ask, args=(self.irc.privmsg, chan, nick, ' '.join( line[1:] ), self)).start()

	def parse_admin(self, line, nick, mask):
		line = line.strip('\x01')
		split = line.split()
		command = split[0].lower()

		if command == 'owner' and len(split) > 1:
			if self.ownerkey is not None:
				self.is_new_owner(split[1].strip(), nick, mask)
		elif command == 'isop' and len(split) > 1:
			for chan in split[1:]:
				if users.is_owner(self, mask) or users.get_chan_access(self, chan, mask) <= 30: self.irc.send('CHANSERV OP %s' %chan)

	def parse_notice(self, recv, split, nick, mask, line):
		pass

	def is_new_owner(self, key, nick, mask):
		if key == self.ownerkey:
			self.users[mask] = {'owner': True, 'created': time.time()}
			self.ownerkey = None
			self.irc.privmsg(nick, 'Hello, master. (%s)' %mask)
			users.save(self)

	def extract_command(self, line):
		# line starts with bot's name
		if line[0].startswith(':%s' %self.irc.nick):
			command = line[1]
			args = line[2:] if len(line) > 2 else []
			bottalk = True
		# line starts with !command
		elif line[0].startswith(':%s' %self.triggerchar):
			# ignore if we are not the main bot
			if self.irc.mynick != self.irc.nick: return None, None, None
			command = line[0][1:].strip( self.triggerchar )
			args = line[1:] if len(line) > 1 else []
			bottalk = False
		# nothing for the bot
		else: return None, None, None
		return command, args, bottalk

	def get_matching_commands(self, command):
		matches = {}
		if not command: return matches
		if command.find(':') != -1:
			try:
				plugin, command = command.split(':')
				if plugin in self.pmlist.keys(): return { plugin: [command] }
			except: pass
			return {}

		for p in self.pmlist.keys():
			m = [ i for i in self.pmlist[p] if i.startswith(command) ]
			if len(m): matches[p] = m
		return matches

	def _run(self):
		self.irc.authed = False
		if self.irc.connect() is False: return
		while self.running:
			recv = self.irc.recvline()
			if recv is False: break
			elif recv is not None:
				split = recv.split(' ')
				self._loop_events(split, recv)

				if split[1] == 'PRIVMSG' or split[1] == 'NOTICE':
					chan = split[2]
					nick, mask = misc.nickmask(split[0])
					if mask is None: continue
					line = split[3:]
					linestr = ' '.join(line)[1:]

					# ignored nick/string
					if misc.is_ignored_nick(self, nick) or misc.is_ignored_string(self, chan, linestr):
						return

					elif split[1] == 'PRIVMSG':
						# ctcp message
						if linestr.startswith('\x01'):
							# make sure we're the target, and the ctcp message is well formatted
							if chan == self.irc.nick and linestr.find('\x01') != -1:
								self.parse_admin(linestr, nick, mask)
						# private non-ctcp message
						elif chan == self.irc.nick:
							if self.ownerkey is not None:
								self.is_new_owner(line[0], nick, mask)
						# message on channel
						else:
							self.parse_privmsg(recv, split, chan, nick, mask, line)

					elif split[1] == 'NOTICE':
						# ignore public notices
						if chan.find('#') != -1: continue
						# private notice
						elif chan == self.irc.nick: self.parse_notice(recv, split, nick, mask, line)

				elif split[1] == '001':
					if not os.path.exists('%s/users.json' %self.datadir):
						self.ownerkey = ''.join( random.sample( string.letters, 20 ))
						print('No access file available. Use `/ctcp %s owner %s` to auth to the bot' % (self.irc.nick, self.ownerkey) )


	def load_plugins(self):
		self.pmlist = dict()
		for plugin in self.pm.get_available_plugins():
			self.pm.load_plugin(plugin)
			res = self.pm.init_plugin(plugin, self)
			if res and 'self' in res: self = res['self']
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
	parser.add_argument('--oper', help="provide oper user password", type=str, default=None, required=False)

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
		args.oper = os.getenv('OPER', None)

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
