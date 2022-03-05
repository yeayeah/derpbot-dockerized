from derpbot import get_user_access
import misc

def event_opmodes(arr):
	if arr['event'] == 'JOIN':
		self = arr['self']
		split = arr['recv'].split(' ')
		chan = split[2].lstrip(':')
		nick, mask = misc.nickmask(split[0])
		access = get_user_access(self, mask)
		if access is None: return
		elif access <= 10: self.irc.send('MODE %s +o %s' % (chan,nick))
		elif access <= 20: self.irc.send('MODE %s +v %s' % (chan,nick))

def action_opmodes(arr):
	if arr['command'] == 'provides': return [ 'op', 'deop', 'voice', 'devoice', 'ban', 'deban', 'topic' ]

	self = arr['self']

	# if user doesnt have op access
	if not misc.isop(self, arr['chan'], arr['nick']):
		access = get_user_access(self, arr['mask'])
		if access > 10: return None
	
	if arr['args'] is not None and len(arr['args']): args = arr['args']
	else: args = [ arr['nick'] ]
	args = [ a for a in args if len(a) ]
	cmd = arr['command']
	chan = arr['chan']

	if cmd == 'topic':
		if len(args): self.irc.socket.send('TOPIC %s :%s\n' % (chan, ' '.join(args)))
		return None

	sign = None
	modes = ''
	nicks = ''

	sign = '-' if cmd.startswith('de') else '+'

	if cmd.endswith('op'): mode = 'o'
	elif cmd.endswith('voice'): mode = 'v'
	elif cmd.endswith('ban'): mode = 'b'

	modes = mode*len(args)
	nicks = ' '.join(args)
	self.irc.socket.send('MODE %s %s%s %s\n' % (chan, sign, modes, nicks))
	return None

