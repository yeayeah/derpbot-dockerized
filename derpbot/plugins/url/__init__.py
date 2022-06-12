from soup_parser import soupify
import re
import time
import random
import misc
import threading

def _get_url_title(uri, proxies=None):
	def _format(string):
		string = string.encode('utf-8') if isinstance(string, unicode) else string
		string = string.replace('\n', ' ')
		return string

	filetype = misc.file_get_contents_type(uri, proxies=proxies)
	if not filetype or filetype.lower().find('html') == -1: return None, None

	res = misc.file_get_contents(uri, proxies=proxies)
	if not res: return None, None
	else: title, desc = (None, None)

	soup = soupify(res)
	try: title = _format(soup.body.find('title').get_text())
	except: pass

	d = soup.find('meta', property='og:description')
	desc = d['content'] if d else None
	if desc: desc = _format(desc)
	return title, desc

def _update_self(self, chan):
	if not hasattr(self, 'settings'): self.settings = dict()
	if not chan in self.settings: self.settings[chan] = dict()
	if not 'p_url' in self.settings[chan]: self.settings[chan]['p_url'] = []
	return self

def __process_to_chan(uri, chan, self):
	title, desc = _get_url_title(uri, proxies=self.args.http_proxy)

	if desc is None and title is None: return
	elif nuri is not None: self.irc.privmsg(chan, nuri)

	j = title if title is not None else desc
	self.irc.privmsg(chan, '^ %s' %j)

def event_url(arr):
	if arr['event'] != 'PRIVMSG': return None

	self = arr['self']
	if self.irc.nick != self.irc.mynick: return None

	split = arr['recv'].split(' ')
	chan = split[2]
	self = _update_self(self, chan)
	line =  ' '.join( split[3:] ).lstrip(':')

	for uri in line.split(' '):
		if uri.find('://') == -1: continue
		domain = uri.split('/')[2]
		if domain.find('/') != -1: domain, _ = domain.split('/')
		skip = False
		for rgx in self.settings[chan]['p_url']:
			if not re.search(rgx, uri): continue
			skip = True
			break
		if skip: continue
		nuri = misc._inspect_uri(uri)
		check = nuri if nuri is not None else uri
		threading.Timer(0, __process_to_chan, args=(uri=check, chan=chan, self=self)).start()

def action_url(arr):
	provides = ['title', 'ud', 'ignore']
	if arr['command'] == 'provides': return provides
	elif not arr['command'] in provides: return

	chan = arr['chan']
	nick = arr['nick']
	self = _update_self(arr['self'], chan)
	if arr['command'] == 'title':

		for uri in arr['args']:
			if uri.find('://') == -1: continue
			_,_, domain = uri.split('/')
			if domain.find('/') != -1: domain, _ = domain.split('/')
			skip = False
			for rgx in self.settings[chan]['p_url']:
				if not re.search(rgx, uri): continue
				skip = True
				break
			if skip: continue
			nuri = misc._inspect_uri(uri)
			check = nuri if nuri is not None else uri
			title, desc = _get_url_title(check, proxies=self.args.http_proxy)

			if title is None: continue
			elif nuri is not None: self.irc.privmsg(chan, nuri)

			self.irc.privmsg(chan, '^ %s' % title)
			time.sleep(0.5)
		return None

	elif arr['command'] == 'ud':
		arg = '+'.join(arr['args'])
		uri = 'https://www.urbandictionary.com/define.php?term=%s' %arg
		_, desc = _get_url_title(uri, proxies=self.args.http_proxy)
		if desc: self.irc.privmsg(chan, '%s' % desc)
		return None

	elif arr['command'] == 'ignore':
		if arr['args'][0] == 'add':
			added = []
			foo = [ i for i  in arr['args'][1:] if not i in self.settings[chan]['p_url'] ]
			if len(foo):
				self.settings[chan]['p_url'].extend(foo)

		elif arr['args'][0] == 'del':
			self.settings[chan]['p_url'] = [ i for i in self.settings[chan]['p_url'] if not i in arr['args'][1:] ]

		elif arr['args'][0] == 'list':
			_l = [ i for i in self.settings[chan]['p_url'] ]
			if len(_l): self.irc.privmsg(chan, '`%s`' % '`, `'.join(_l))

	return {'self': self, 'reply': 'Ok.'}
