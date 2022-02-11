from derpbot import get_user_access
import rocksock
from http2 import RsHttp, _parse_url
import os
import plugins
import time

def action_plugin(arr):
	if arr['command'] == 'provides': return ['install', 'load', 'unload', 'reload', 'replace', 'list', 'help']
	self = arr['self']

	if arr['command'] == 'help':
		if len(arr['args']) > 1:
			name = arr['args'][1]
			if name in self.pmlist.keys():
				return { 'reply': '%s: %s' % (name, ', '.join(self.pmlist[name])), 'self':self }
		else:
			for name in self.pmlist.keys():
				if name is None: continue
				self.irc.socket.send('PRIVMSG %s :%s: %s\n' % (arr['chan'], name, ', '.join( self.pmlist[name])))
				time.sleep(0.3)

	elif arr['command'] == 'list':
		for name in self.pmlist.keys():
			if name is None: continue
			print('plugin %s provides %s' % (name, self.pmlist[name]))
			self.irc.socket.send('PRIVMSG %s :%s: %s\n' % (arr['chan'], name, ', '.join( self.pmlist[name])))
			time.sleep(0.3)

	elif arr['command'] == 'install' or arr['command'] == 'replace':
		if get_user_access(self, arr['mask']) > 5: return None
		if len(arr['args']) < 3 or arr['args'][1].find('as') == -1: return {'reply': 'error; use: plugin:install <url> as <name>', 'self': self }
		name = arr['args'][2]
		if arr['command'] == 'install' and os.path.exists('plugins/%s' %name): return  {'reply': 'error: plugin with same name exists; you might want to use `plugin:replace`?', 'self': self }
		plugin = arr['args'][0]
		if plugin.find('://') != -1:
			host, port, ssl, uri = _parse_url(plugin)
			proxies = None
			http = RsHttp(host,ssl=ssl,port=port, keep_alive=True, follow_redirects=True, auto_set_cookies=True, proxies=proxies, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0')
			if not http.connect(): return {'reply': 'error, failed to fetch from url', 'self': self }
			hdr, res = http.get(uri, headers)
			res = res.encode('utf-8') if isinstance(res, unicode) else res
		else:
			if not os.path.exists('plugins-available/%s/__init__.py' %plugin):
				return {'reply': 'error; plugin "%s" does not exist', 'self': self }
			with open('plugins-available/%s/__init__.py'%plugin, 'r') as r:
				res = ''.join( r.readlines() )

		if not os.path.exists('plugins/%s' %name): os.makedirs('plugins/%s' %name)
		with open('plugins/%s/__init__.py' %name, 'w') as h: h.write(res)
		return {'reply': 'plugin "%s" (re)installed as "%s"' % (plugin, name), 'self': self }

	elif arr['command'] == 'load':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']): return {'reply': 'error; use: plugin:load <name>' }
		for name in arr['args']:
			print('going with plugin "%s"' %name)
			if not os.path.exists('plugins/%s' %name): return {'reply': 'error: plugin "%s" not found' }
			elif name in self.pmlist: return  {'reply': 'plugin "%s" already loaded; you might want to use `plugin:reload`?' }
			try: self.pm.load_plugin(name)
			except Exception as e: return {'reply': 'error; cannot load plugin "%s" (%s)' % (name, e) }

			try: provides = self.pm.execute_action_hook(name, { 'command': 'provides', 'self': self })
			except: provides = [ name ]
			finally: self.pmlist[name] = provides
		return {'reply': 'plugin "%s" provides "%s"' %(name, ', '.join(provides)), 'self': self }

	elif arr['command'] == 'unload':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']) > 1: return {'reply': 'error; use: plugin:load <name>' }
		for name in arr['args'][1:]:
			if name in self.pmlist:
				self.pm.unload_plugin(name)
				self.pmlist.pop(name, None)
		return {'res': 'Success, i guess.', 'self': self }
		
	elif arr['command'] == 'reload':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']) > 1: return {'reply': 'error; use: plugin:load <name>' }
		for name in arr['args'][1:]:
			if name in self.pmlist: 
				self.pm.unload(name)
				self.pmlist.pop(name, None)
				self.pm.load_plugin(name)
				try: provides = self.pm.execute_action_hook(name, { 'command': 'provides' })
				except: provides = [ name ]
				finally: self.pmlist[plugin] = provides
		return {'res': 'Success, i guess.', 'self': self }
