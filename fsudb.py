import sqlite3
import time
import os

db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'fsu.db'), check_same_thread = False)
cur = db.cursor()

class DBError(Exception):
	pass

class NoSuchEntity(DBError):
	pass

class TooManyEntities(DBError):
	pass

def _instantiate(cls, rows, attrib, val):
	if not rows:
		raise NoSuchEntity(cls, attrib, val)
	if len(rows)>1:
		raise TooManyEntities(cls, attrib, val)
	return cls(*rows[0])

class Log(object):
	@staticmethod
	def Log(src, act, attrib, oldval, val, detail):
		if isinstance(act, Account):
			act = act.aid
		cur.execute('INSERT INTO log (time, src, aid, attrib, oldval, val, detail) VALUES (?, ?, ?, ?, ?, ?, ?)', (time.time(), src, act, attrib, oldval, val, detail.decode('utf8')))
		db.commit()
	@staticmethod
	def All():
		cur.execute('SELECT time, src, aid, attrib, oldval, val, detail FROM log')
		return cur.fetchall()

class Account(object):
	def __init__(self, aid, name, balance, dispid=None, hidden=None):
		self.aid = aid
		self.name = name
		self.balance = balance
		self.dispid = dispid
		self.hidden = hidden
		self._aid = aid
		self._name = name
		self._balance = balance
		self._dispid = dispid
		self._hidden = hidden
		if dispid is None:
			self.dispid = aid
		if hidden is None:
			self.hidden = 0
	@classmethod
	def FromID(cls, aid):
		cur.execute('SELECT aid, name, balance, dispid, hidden FROM accounts WHERE aid=?', (aid,))
		return _instantiate(cls, cur.fetchall(), 'aid', aid)
	@classmethod
	def All(cls):
		ret = []
		for row in cur.execute('SELECT aid, name, balance, dispid, hidden FROM accounts'):
			ret.append(cls(*row))
		return ret
	@classmethod
	def Create(cls, name, balance, src=None, hidden=None):
		cur.execute('INSERT INTO accounts (name, balance, hidden) VALUES (?, ?, ?)', (name, balance, hidden))
		Log.Log(src, cur.lastrowid, 'aid', None, cur.lastrowid, '%r: %r created account %r'%(time.time(), src, cur.lastrowid))
		db.commit()
		return cls(cur.lastrowid, name, balance)
	def Update(self, src=None):
		for attr in ('aid', 'name', 'balance', 'dispid', 'hidden'):
			if getattr(self, attr) != getattr(self, '_'+attr):
				Log.Log(src, self, attr, getattr(self, '_'+attr), getattr(self, attr), '%r: %r changed %r %s from %r to %r'%(time.time(), src, self, attr, unicode(getattr(self, '_'+attr)).encode('utf8', 'replace'), unicode(getattr(self, attr)).encode('utf8', 'replace')))
		cur.execute('UPDATE accounts SET name=?, balance=?, dispid=?, hidden=? WHERE aid=?', (self.name, self.balance, self.dispid, self.hidden, self.aid))
		db.commit()
	def Delete(self, src=None):
		cur.execute('DELETE FROM accounts WHERE aid=?', (self.aid,))
		Log.Log(src, self, 'aid', self.aid, None, '%r: %r deleted %r'%(time.time(), src, self))
		db.commit()
	def __repr__(self):
		return '<Account %s (%d)"%s" %s =%f>'%(self.aid, self.dispid, self.name.encode('utf8', 'replace'), '(hidden)' if self.hidden else 0, self.balance)
