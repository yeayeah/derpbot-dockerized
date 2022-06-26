import time
import hashlib
import random
import misc

def init_quote(arr):
	if not 'self' in arr or not arr['self']: return
	self = arr['self']
	if not hasattr(self, 'quotes'):
		if os.path.isfile('%s/quotes.json' %self.datadir): self.quotes = misc.filetojson('%s/quotes.json' %self.datadir)
		else: self.quotes = dict()
	return {'self': self}

def event_quote(arr):
	provides = ['PRIVMSG']
	if arr['command'] == 'provides': return provides
	elif not arr['event'] in provides: return None
	elif arr['self'].irc.nick != arr['self'].irc.mynick: return None

	self = arr['self']
	split = arr['recv'].split(' ')
	chan = split[2]
	line =  ' '.join( split[3:] ).lstrip(':')
	if line.find('#quote') != -1 and len(self.quotes.keys()):
		quoteid = random.choice(self.quotes.keys())
		quote = self.quotes[quoteid]
		self.irc.action(chan, '#%s (%s)' % (quoteid[:10], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(quote['added']))))
		self.irc.privmsg(chan, quote['message'])

def action_quote(arr):
	if arr['command'] == 'provides': return ['add', 'del']

	self = arr['self']
	chan = arr['chan']
	nick = arr['nick']
	if arr['command'] == 'add':
		message = ' '.join( arr['args'] )
		md5sum = hashlib.md5(message.lower().strip()).hexdigest()

		if not md5sum in self.quotes:
			self.quotes[md5sum] = {
				'message': message,
				'added': time.time()
			}
			misc.jsontofile('%s/quotes.json' %self.datadir, self.quotes)
			return {'reply': 'Quote #%s saved.' %md5sum[:10], 'self': self }
	
	elif arr['command'] == 'del':
		deleted = list()
		foobar = self.quotes
		for qid in foobar.keys():
			for arg in arr['args']:
				if qid[:10] != arg: continue
				deleted.append(qid)
				break
		if len(deleted):
			for d in deleted: del(self.quotes[d])
			misc.jsontofile('%s/quotes.json' %self.datadir, self.quotes)
			self.irc.privmsg(chan, 'deleted `%s`' %'`, `'.join([d[:10] for d in deleted]))

	elif len(self.quotes):
		quoteid = random.choice(self.quotes.keys())
		quote = self.quotes[quoteid]
		self.irc.action(chan, '%s (%s) : %s' % (quote['nick'], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(quote['added'])), quoteid))
		self.irc.privmsg(chan, quote['message'])

	return {'self': self}
