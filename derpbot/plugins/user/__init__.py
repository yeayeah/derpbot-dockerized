import os
import plugins
import users

def action_user(arr):
	if arr['command'] == 'provides': return ['add', 'del', 'list']
	self = arr['self']
	nick = arr['nick']
	mask = arr['mask']
	chan = arr['chan']

	if not users.is_owner(self, mask):
		access = users.get_chan_access(self, chan, mask)
		if access is None: return None

	elif arr['command'] == 'add':
		mask, level = arr['args']
		try: level = int(level)
		except: return {'reply': 'error, level has to be numeric.'}
		if access < level: return {'reply':'You may not.'}

		res = users.add(self, chan, mask, level)
		if res:
			self = res
			return {'self': self, 'reply': 'User `%s` added with level `%s`.' % (mask, level)}

	elif arr['command'] == 'del':
		deleted = list()
		for mask in arr['args']:
			mask = mask.strip()
			maccess = users.get_chan_access(self, chan, mask)
			if access < maccess: continue
			res = users.delete(self, chan, mask)
			if res is not False:
				self = res
				deleted.append(mask)
		return {'self': self, 'reply': 'removed mask(s) `%s`.' % '`, `'.join(deleted)}

	elif arr['command'] == 'list':
		line = ''
		for mask in self.users:
			if chan in self.users[mask]:
				if len(line): line = '%s, %s: %d' % (line, mask, self.users[mask][chan])
				else: line = '%s: %d' % (mask, self.users[mask][chan])
		self.irc.notice(nick, line)
