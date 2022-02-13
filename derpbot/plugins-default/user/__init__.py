from derpbot import get_user_access
import os
import plugins

def action_user(arr):
	if arr['command'] == 'provides': return ['add', 'del', 'list']
	self = arr['self']
	if get_user_access(self, arr['mask']) > 5: return None

	if not os.path.exists('%s/access' % self.datadir):
		self.irc.privmsg(arr['chan'], 'Error: no access file..')

	elif arr['command'] == 'add':
		username, level = arr['args']
		if get_user_access(self, username) is not None: return {'reply': 'error, conflicting...' }
		with open('%s/access' %self.datadir, 'a') as h: h.write('%s %s\n' % (username, level))

	elif arr['command'] == 'del':
		with open('%s/access'% self.datadir, 'r') as r:
			users = dict()
			for l in r.readlines():
				l = l.strip()
				u, l = l.split(' ')
				users[u] = l

		with open('%s/access'%self.datadir, 'w') as h:
			for user in users.keys():
				if not user in arr['args']:
					h.write('%s %s\n' % (user, users[user]))

	elif arr['command'] == 'list':
		with open('%s/access'%self.datadir, 'r') as r:
			for l in r.readlines():
				self.irc.privmsg(arr['nick'], l.strip())
