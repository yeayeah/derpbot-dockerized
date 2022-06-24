import misc
import users

def event_opmodes(arr):
	provides = ['JOIN']
	if arr['command'] == 'provides': return provides
	elif arr['event'] == 'JOIN':
		self = arr['self']
		split = arr['recv'].split(' ')
		chan = split[2].lstrip(':')
		nick, mask = misc.nickmask(split[0])
		if nick == self.irc.nick: return
		access = users.get_chan_access(self, chan, mask)
		if access is not None:
			if access <= 10: self.irc.send('MODE %s +o %s' % (chan,nick))
			elif access <= 20: self.irc.send('MODE %s +h %s' % (chan,nick))
			elif access <= 30: self.irc.send('MODE %s +v %s' % (chan, nick))

def action_opmodes(arr):
	if arr['command'] == 'provides': return [ 'op', 'deop', 'voice', 'devoice', 'ban', 'deban', 'topic', 'up', 'down' ]

	self = arr['self']
	chan = arr['chan']
	nick = arr['nick']
	mask = arr['mask']

	if arr['command'] == 'up' or arr['command'] == 'down':
		access = users.get_chan_access(self, chan, mask)
		if access is not None:
			sign = '+' if arr['command'] == 'up' else '-'
			if access <= 10: self.irc.send('MODE %s %so %s' % (chan, sign, nick))
			elif access <= 20: self.irc.send('MODE %s %sh %s' % (chan, sign, nick))
			elif access <= 30: self.irc.send('MODE %s %sv %s' % (chan, sign, nick))
		return

	if users.is_owner(self, mask): access = 0
	else: access = users.get_chan_access(self, chan, mask)
	if access > 20: return None
	
	if arr['args'] is not None and len(arr['args']): args = arr['args']
	else: args = [ arr['nick'] ]
	args = [ a for a in args if len(a) ]
	cmd = arr['command']

	if cmd == 'topic':
		if len(args): self.irc.socket.send('TOPIC %s :%s\n' % (chan, ' '.join(args)))
		return None

	sign = None
	modes = ''
	nicks = ''

	sign = '-' if cmd.startswith('de') else '+'

	if cmd.endswith('op') and access <= 10: mode = 'o'
	elif cmd.endswith('ban') and access <= 10: mode = 'b'
	elif cmd.endswith('voice'): mode = 'v'
	else: return

	modes = mode*len(args)
	nicks = ' '.join(args)
	self.irc.socket.send('MODE %s %s%s %s\n' % (chan, sign, modes, nicks))
