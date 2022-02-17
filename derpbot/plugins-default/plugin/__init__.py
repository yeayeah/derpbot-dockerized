from derpbot import get_user_access
import os
import plugins
import time
import misc

def action_plugin(arr):
	if arr['command'] == 'provides': return ['install', 'load', 'unload', 'reload', 'replace', 'help']
	self = arr['self']

	if arr['command'] == 'help':
		if len(arr['args']) >= 1:
			for name in arr['args']:
				if name in self.pmlist.keys():
					return { 'reply': '`%s` provides actions `%s`.' % (name, '`, `'.join(self.pmlist[name])), 'self':self }
			return

		else:
			_plugins = []
			for name in self.pmlist.keys():
				if name is not None: _plugins.append(name)

			if len(_plugins):
				self.irc.privmsg(arr['chan'], 'Plugins: `%s`.' % '`, `'.join(_plugins))
				self.irc.privmsg(arr['chan'], 'Use `help <plugin>` to get a list of actions. Use `<plugin>:<action>` if multiple plugins provide the same action.')

	elif arr['command'] == 'install' or arr['command'] == 'replace':
		if get_user_access(self, arr['mask']) > 5: return None
		if len(arr['args']) < 3 or arr['args'][1].find('as') == -1: return {'reply': 'error; use: plugin:install <url> as <name>', 'self': self }
		name = arr['args'][2]
		if arr['command'] == 'install' and os.path.exists('plugins/%s' %name): return  {'reply': 'error: plugin with same name exists; you might want to use `plugin:replace`?', 'self': self }
		plugin = arr['args'][0]
		if plugin.find('://') != -1:
			res = misc.file_get_contents(plugin, proxies=self.args.http_proxy)
		else:
			if not os.path.exists('plugins-available/%s/__init__.py' %plugin):
				return {'reply': 'error; plugin `%s` does not exist', 'self': self }
			with open('plugins-available/%s/__init__.py'%plugin, 'r') as r:
				res = ''.join( r.readlines() )

		if not os.path.exists('plugins/%s' %name): os.makedirs('plugins/%s' %name)
		with open('plugins/%s/__init__.py' %name, 'w') as h: h.write(res)
		return {'reply': 'plugin `%s` (re)installed as `%s`' % (plugin, name), 'self': self }

	elif arr['command'] == 'load':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']): return {'reply': 'error; use: plugin:load <name>' }
		for name in arr['args']:
			if not os.path.exists('plugins/%s' %name): return {'reply': 'error: plugin `%s` not found'%name }
			elif name in self.pmlist: return  {'reply': 'plugin `%s` already loaded; you might want to use `plugin:reload`?' }
			try: self.pm.load_plugin(name)
			except Exception as e: return {'reply': 'error; cannot load plugin `%s` (%s)' % (name, e) }

			try: provides = self.pm.execute_action_hook(name, { 'command': 'provides', 'self': self })
			except: provides = [ name ]
			finally: self.pmlist[name] = provides
		return {'reply': 'plugin `%s` provides `%s`' %(name, '`, `'.join(provides)), 'self': self }

	elif arr['command'] == 'unload':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']) >= 1: return {'reply': 'error; use: `plugin:unload <name>`' }
		for name in arr['args']:
			if name in self.pmlist:
				self.pm.unload_plugin(name)
				self.pmlist.pop(name, None)
		return {'res': 'Success, i guess.', 'self': self }
		
	elif arr['command'] == 'reload':
		if get_user_access(self, arr['mask']) > 5: return None
		elif not len(arr['args']) >= 1: return {'reply': 'error; use: `plugin:reload <name>`' }
		for name in arr['args']:
			if name in self.pmlist: 
				self.pm.unload(name)
				self.pmlist.pop(name, None)
				self.pm.load_plugin(name)
				try: provides = self.pm.execute_action_hook(name, { 'command': 'provides' })
				except: provides = [ name ]
				finally: self.pmlist[plugin] = provides
		return {'res': 'Success, i guess.', 'self': self }
