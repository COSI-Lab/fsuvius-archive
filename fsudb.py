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
		cur.execute('INSERT INTO log (time, src, aid, attrib, oldval, val, detail) VALUES (?, ?, ?, ?, ?, ?, ?)', (time.time(), src, act, attrib, oldval, val, detail))
		db.commit()
	@staticmethod
	def All():
		cur.execute('SELECT time, src, aid, attrib, oldval, val, detail FROM log')
		return cur.fetchall()

class Account(object):
	def __init__(self, aid, name, balance):
		self.aid = aid
		self.name = name
		self.balance = balance
		self._aid = aid
		self._name = name
		self._balance = balance
	@classmethod
	def FromID(cls, aid):
		cur.execute('SELECT aid, name, balance FROM accounts WHERE aid=?', (aid,))
		return _instantiate(cls, cur.fetchall(), 'aid', aid)
	@classmethod
	def All(cls):
		ret = []
		for row in cur.execute('SELECT aid, name, balance FROM accounts'):
			ret.append(cls(*row))
		return ret
	@classmethod
	def Create(cls, name, balance, src=None):
		cur.execute('INSERT INTO accounts (name, balance) VALUES (?, ?)', (name, balance))
		Log.Log(src, cur.lastrowid, 'aid', None, cur.lastrowid, '%r: %r created account %r'%(time.time(), src, cur.lastrowid))
		db.commit()
		return cls(cur.lastrowid, name, balance)
	def Update(self, src=None):
		for attr in ('aid', 'name', 'balance'):
			if getattr(self, attr) != getattr(self, '_'+attr):
				Log.Log(src, self, attr, getattr(self, '_'+attr), getattr(self, attr), '%r: %r changed %r %s from %r to %r'%(time.time(), src, self, attr, getattr(self, '_'+attr), getattr(self, attr)))
		cur.execute('UPDATE accounts SET name=?, balance=? WHERE aid=?', (self.name, self.balance, self.aid))
		db.commit()
	def Delete(self, src=None):
		cur.execute('DELETE FROM accounts WHERE aid=?', (self.aid,))
		Log.Log(src, self, 'aid', self.aid, None, '%r: %r deleted %r'%(time.time(), src, self))
		db.commit()
	def __repr__(self):
		return '<Account %s "%s" =%f>'%(self.aid, self.name, self.balance)
