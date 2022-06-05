import time
import re
import users

def _ignore_exists(self, chan, type, str):
	if not type in self.settings[chan]['ignore']: return False

	for i in self.settings[chan]['ignore'][type]:
		if re.search(i, str): return True
	return False

def action_ignore(arr):
	provides = ['add', 'del', 'list']
	if arr['command'] == 'provides': return provides
	elif not arr['command'] in provides: return None
	elif not misc.isop(self, arr['chan'], arr['nick']):
		if users.get_user_access(self, arr['mask']) > 10: return None

	_types = [ 'nick', 'string', 'mask' ]
	self = arr['self']
	chan = arr['chan']

	if not chan in self.settings: self.settings[chan] = dict()
	if not 'ignore' in self.settings[chan]: self.settings[chan]['ignore'] = dict()

	if arr['command'] == 'list':
		args = arr['args'] if len(arr['args']) else _types
		for t in args:
			if not t in self.settings[chan]['ignore']: continue
			elements = [ i for i in self.settings[chan]['ignore'][t] ]
			if len(elements): self.irc.privmsg(chan, '`%s`: `%s`' % (t, '`, `'.join( elements )))
			time.sleep(0.5)
		return {'self': self}

	if len(arr['args']) < 2: return {'reply': 'Error, needs arguments.'}
	elif not arr['args'][0] in _types: return {'reply': 'Unknown ignore type `%s`. (avail: `nick`, `string`, `mask`)'}

	_type = arr['args'][0]
	elements = arr['args'][1:]

	if arr['command'] == 'add':
		added = []
		if not _type in self.settings[chan]['ignore']: self.settings[chan]['ignore'][_type] = []

		for element in elements:
			if _ignore_exists(self, chan, _type, element): continue
			self.settings[chan]['ignore'][_type].append(element)
			added.append( element )

		if len(added): self.irc.privmsg(arr['chan'], '`%s`: added `%s`' % (_type, ','.join(added)))

	elif arr['command'] == 'del':
		#if len(arr['args']) < 2: return
		deleted = []
		for element in elements:
			if _ignore_exists(self, chan, _type, element):
				del(self.settings[chan]['ignore'][_type][element])
				deleted.append(element)

		if len(deleted): self.irc.privmsg(arr['chan'], '`%s`: deleted `%s`' % (_type, '`, `'.join(added)))

	return {'self': self}
