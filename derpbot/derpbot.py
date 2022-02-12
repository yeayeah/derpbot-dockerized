#!/usr/bin/env python

import myirc
import threading
import rocksock
import plugins
import argparse
import os
import random
import string

class Derpbot():
	def __init__(self, server, port, nick, chan, triggerchar='!', ssl=False, auth=None, proxies=None, args=None):
		self.server = server
		self.args = args
		self.port = port
		self.nick = nick
		self.mynick = nick
		self.chan = chan
		self.irc = None
		self.ssl = ssl
		self.auth = auth
		self.proxies = proxies
		self.triggerchar = triggerchar
		self.datadir = 'data/%s' %self.server
		self.running = True
		self.threads = []
		self.ownerkey = None
		self.pm = plugins.PluginManager('./plugins') if os.path.isdir('./plugins') else None

	def run(self):
		if self.pm is not None: self.load_plugins()
		else: self.pmlist = dict()
		self.irc = myirc.IRC(self.server, self.port, self.nick, self.chan, self.ssl, self.proxies, self.auth)
		while self.running:
			self._run()
			try: self.irc.disconnect()
			except: pass
	
	def _run(self):
		self.irc.connect()
		while self.running:
			recv = self.irc.get_event('001|JOIN|PRIVMSG|NOTICE|INVITE')
			if recv is False: break
			split = recv.split(' ')
			if split[1] == '001':
				if not os.path.exists('%s/access' %self.datadir):
					self.ownerkey = ''.join( random.sample( string.letters, 10 ))
					print('No access file available. Use `/msg %s %s` to auth to the bot' % (self.irc.nick, self.ownerkey) )

			elif split[1] == 'INVITE':
				user, mask = nickmask(split[0])
				if get_user_access(self, mask) > 5: continue
				self.irc.send('JOIN %s' %split[3].lstrip(':'))

			elif split[1] == 'JOIN':
				chan = split[2].lstrip(':')
				nick, mask = nickmask(split[0])
				access = get_user_access(self, mask)
				if access is None: continue
				elif access <= 10: self.irc.send('MODE %s +o %s' % (chan,nick))
				elif access <= 20: self.irc.send('MODE %s +v %s' % (chan,nick))

			# bot command ?
			elif split[1] == 'PRIVMSG':
				chan = split[2].lstrip(':')
				nick, mask = nickmask(split[0])
				if chan == self.irc.nick:
					if self.ownerkey is None: continue
					key = split[3][1:]
					if key == self.ownerkey:
						if not os.path.exists('%s/access' %self.datadir):
							with open('%s/access' %self.datadir, 'w') as h:
								h.write('%s 0\n' %mask)
							self.irc.send('PRIVMSG %s :Hello, master. (%s)' % (nick, mask))
							self.ownerkey = None
					continue

				line = split[3:]
				linestr = ' '.join(line)
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
					plugin, command = command.split(':')
					if plugin in self.pmlist.keys():
						res = self.run_plugin(nick, chan, mask, plugin, command, args)
						if res is not None:
							if 'reply' in res and res['reply']: self.irc.send('PRIVMSG %s :%s' % (chan, res['reply']))
							if 'self' in res and res['self']: self = res['self']
						continue

				for p in self.pmlist.keys():
					m = [ i for i in self.pmlist[p] if i.startswith(command) ]
					if len(m): matches[p] = m

				if len(matches.keys()) == 1 and len(matches[ matches.keys()[0] ]) == 1:
					res = self.run_plugin( nick, chan, mask, matches.keys()[0], matches[matches.keys()[0]][0], args)
					if res is not None:
						if 'reply' in res and res['reply']: self.irc.send('PRIVMSG %s :%s' % (chan, res['reply']))
						if 'self' in res and res['self'] is not None: self = res['self']

				elif len(matches.keys()) > 1:
					self.irc.send('PRIVMSG %s :%s: Ambiguous command, "%s" offer command %s.' % (chan, nick, ', '.join( matches.keys()), command))
					self.irc.send('PRIVMSG %s :%s: Use "plugin_name:command" if multiple plugins offer the same command.' % (chan, nick))
					
				# user wants to talk ?
				elif bottalk:
					print('user needs to talk')


	def load_plugins(self):
		self.pmlist = dict()
		for plugin in self.pm.get_available_plugins():
			self.pm.load_plugin(plugin)
			try: provides = self.pm.execute_action_hook(plugin, { 'command': 'provides' })
			except: provides = [ plugin ]
			finally: self.pmlist[plugin] = provides

			print('plugin %s provides: %s' % (plugin, provides))

	def stop(self):
		threads = [ t for t in self.threads if t.is_alive() ]
		if len(threads): threads.join()
		if self.irc: self.irc.send('QUIT :leaving')
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

def get_user_access(self, mask):
	if not os.path.isfile('data/%s/access' % self.server): return None
	with open('data/%s/access' %self.server, 'r') as h:
		for l in h.readlines():
			l = l.strip()
			host, access = l.split(' ')
			if mask.find(host) != -1: return int(access)

def nickmask(data):
	_, line = data.split(':')
	return line.split('!')

if __name__ == '__main__':
	if not os.path.exists('plugins'): os.popen('mkdir plugins')
	if not os.path.exists('plugins/plugin'): os.popen('cp -r plugins-default/* plugins/')
	parser = argparse.ArgumentParser()
	parser.add_argument('--dockerized', help="indicates it's run through docker.  Will fetch nick, server, ... over env. variables. (default: True)", type=bool, default=True, required=False)
	parser.add_argument('--nick', help="nickname to use", type=str, default='derpbot', required=False)
	parser.add_argument('--chan', help="#some,#chan,#to,#join", type=str, default='##derpbot', required=False)
	parser.add_argument('--server', help="irc server to connect", type=str, default="irc.libera.chat", required=False)
	parser.add_argument('--port', help="port to connect to", type=int, default=6697, required=False)
	parser.add_argument('--use-ssl', help="use ssl? (default: true)", type=bool, default=True, required=False)
	parser.add_argument('--auth', help="define username/password to identify to. format 'username password'", type=str, default=None, required=False)
	parser.add_argument('--proxies', help="proxy/ies to use/chain. Format: sock4://127.0.0.1:9050,http://1.2.3.4:8080,...", type=str, default=None, required=False)
	parser.add_argument('--triggerchar', help="trigger char (default: !)", type=str, default='!', required=False)

	args = parser.parse_args()

	if args.dockerized:
		args.nick = os.getenv('NICK', 'derpyderp')
		args.server = os.getenv('SERVER', 'irc.libera.chat')
		args.port = int( os.getenv('PORT', 6697) )
		args.chan = os.getenv('CHAN', '##derpbot')
		args.auth = os.getenv('AUTH', None)
		args.use_ssl = bool(os.getenv('SSL', 1))
		args.proxies = os.getenv('PROXIES', None)
		args.triggerchar = os.getenv('TRIGGERCHAR', '!')

	if not os.path.exists('data/%s' %args.server):
		try:
			os.makedirs('data/%s' %args.server)
		except Exception as e:
			print('ERROR: cannot create "data/%s" directory' %args.server)
			raise


	proxies = [ rocksock.RocksockProxyFromURL(i.strip()) for i in args.proxies.split(';') ] if args.proxies else None
	derp = Derpbot(server=args.server, port=args.port, nick=args.nick, chan=args.chan, ssl=args.use_ssl, auth=args.auth, proxies=proxies, triggerchar=args.triggerchar, args=args)

	try: derp.run()
	except KeyboardInterrupt: pass
	#except Exception as e: print('error: %s' %e)
	finally: derp.stop()
