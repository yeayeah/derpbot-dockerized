import os

def get_user_access(self, mask):
	if not os.path.isfile('data/%s/access' % self.server): return 9999999
	with open('data/%s/access' %self.server, 'r') as h:
		for l in h.readlines():
			host, access = l.strip().split(' ')
			if mask.find(host) != -1: return int(access)
	return None
