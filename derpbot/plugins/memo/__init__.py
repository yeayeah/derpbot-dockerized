import time
import hashlib
from misc import nickmask

def event_memo(arr):
	self = arr['self']
	if not hasattr(self, 'p_tell'): return None
	event = arr['event']

	if event == 'JOIN':

		nick, mask = nickmask( arr['recv'].split(' ')[0] )
		remove = []

		for md5 in self.p_tell.keys():
			_array = self.p_tell[md5]
			if _array['nick_to'] != nick: continue
			self.irc.notice(nick, '`%s` said:' % _array['nick_from'])
			self.irc.notice(nick, _array['message'])
			remove.append(md5)
	
		for i in remove: del self.p_tell[i]

	return {'self': self}

def action_memo(arr):
	if arr['command'] == 'provides': return ['tell', 'remind', 'inbox']

	self = arr['self']
	chan = arr['chan']
	nick = arr['nick']

	if arr['command'] == 'tell':
		if not hasattr(self, 'p_tell'): self.p_tell = dict()

		nick_from = nick
		nick_to = arr['args'][0]
		message = ' '.join( arr['args'][1:] )
		md5sum = hashlib.md5('%s:%s:%s' % (nick_from, nick_to, message)).hexdigest()

		if not md5sum in self.p_tell:
			self.p_tell[md5sum] = {
				'nick_to': nick_to,
				'nick_from': nick_from,
				'message': message,
				'ticks': time.time()
			}

			return {'reply': '%s: message saved.' %nick, 'self': self }
	
	elif arr['command'] == 'remind':
		if not hasattr(self, 'p_remind'): self.p_remind = dict()

		factors = [ 1, 60, 60*60, 60*60*24 ]
		message = ' '.join( arr['args'][1:] )
		delay = 0

		d_split = arr['args'][0].split(':')
		d_split.reverse()

		for i in range(len(d_split)):
			j = int(d_split[i]) * int(factors[i])
			delay += j

		self.irc.privmsg(chan, '%s: %s' %(nick,message), delay)

		return {'reply': '%s: reminder saved.' %nick, 'self': self }
