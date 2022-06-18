import os
import json

def get_user_access(self, mask):
	if not os.path.isfile('data/%s/access' % self.server): return 9999999
	with open('data/%s/access' %self.server, 'r') as h:
		for l in h.readlines():
			host, access = l.strip().split(' ')
			if mask.find(host) != -1: return int(access)

def get_chan_access(self, chan, mask):
	for item in self.users:
		if mask.find(item) != -1:
			return int(self.users[item][chan]) if chan in self.users[item] else None

def is_owner(self, mask):
	for item in self.users:
		if mask.find(item) != -1:
			return True if 'owner' in self.users[item] else False
	return False

def save(self):
	if len(self.users):
		with open('%s/users.json' % self.datadir, 'w') as h:
			json.dump(self.users, h, indent=4)

def add(self, chan, mask, level):
	if not mask in self.users: self.users[mask] = {'created': time.time()}
	self.users[mask][chan] = level
	save(self)
	return self


def delete(self, chan, mask):
	if not mask in self.users: return False
	elif chan in self.users[mask]:
		del( self.users[mask][chan] )
		save(self)
		return self
