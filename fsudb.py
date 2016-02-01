import sqlite3
import time
import uuid

db = sqlite3.connect('fsu.db')
cur = db.cursor()

class DBError(Exception):
    pass

class NoSuchEntity(DBError):
    pass

class TooManyEntities(DBError):
    pass

class DBObject(object):
    __FIELDS__ = ()
    __DEFAULTS__ = {}
    __TABLE__ = ''
    __TYPES__ = {}
    AUTO_COMMIT = True

    def __init__(self, rowid, *data):
        self.rowid = rowid
        for idx, field in enumerate(self.__FIELDS__):
            default = self.__DEFAULTS__[field]
            if idx < len(data):
                setattr(self, field, data[idx])
            else:
                setattr(self, field, default)

    @classmethod
    def CreateTable(cls):
        cur.execute('CREATE TABLE IF NOT EXISTS %(table)s (%(columns)s)'%\
                {'table': cls.__TABLE__,
                 'columns': ', '.join('%s%s'%(field, ' '+cls.__TYPES__[field] if field in cls.__TYPES__ else '') for field in self.__FIELDS__)}
        )

    @classmethod
    def Create(cls, *data):
        row = list(data)
        for field in cls.__FIELDS__[len(data):]:
            row.append(cls.__DEFAULTS__[field])
        cur.execute('INSERT INTO %(table)s VALUES (%(fields)s)'%{
            'table': cls.__TABLE__,
            'fields': ', '.join(['?'] * len(cls.__FIELDS__))
        }, row)
        if self.AUTO_COMMIT:
            db.commit()
        return cls(cur.lastrowid, *row)

    def Delete(self):
        cur.execute('DELETE FROM %(table)s WHERE ROWID=?'%{'table': self.__TABLE__}, (self.rowid,))
        if self.AUTO_COMMIT:
            db.commit()

    def Update(self):
        cur.execute('UPDATE %(table)s SET %(fields)s WHERE ROWID=?'%{
            'table': self.__TABLE__,
            'fields': ', '.join('%s=?'%(field,) for field in self.__FIELDS__)
        }, tuple(getattr(self, field) for field in self.__FIELDS__) + (self.rowid,))
        if self.AUTO_COMMIT:
            db.commit()

    @classmethod
    def Get(cls, **criteria):
        pairs = criteria.items()
        keys = [pair[0] for pair in pairs]
        values = [pair[1] for pair in pairs]
        cur.execute('SELECT ROWID, %(fields)s FROM %(table)s WHERE %(criteria)s'%{
            'table': self.__TABLE__,
            'fields': ', '.join(self.__FIELDS__),
            'criteria': ' and '.join('%s=?'%(k,) for k in keys),
        }, values)
        return [cls(*row) for row in cur]

    @classmethod
    def GetOne(cls, **criteria):
        res = cls.Get(**criteria)
        if len(res) < 1:
            raise NoSuchEntity(cls, criteria)
        elif len(res) > 1:
            raise TooManyEntities(cls, criteria)
        return res[0]

    def __repr__(self):
        return '<%(cls)s(%(table)s %(row)d %(items)s'%{
                'table': self.__TABLE__,
                'cls': type(self).__name__,
                'row': self.rowid,
                'items': ' '.join('%s=%r'%(field, getattr(self, field)) for field in self.__FIELD__),
        }

class Access(DBObject):
    ROOT = '_root'
    __TABLE__ = 'access'
    __FIELDS__ = ('aid', 'type')


class Account(DBObject):
    __TABLE__ = 'accounts'
    __FIELDS__ = ('name', 'dispname', 'balance', 'pwhash')
    __DEFAULTS__ = {'dispname': None, 'balance': 0.0}
    def CanAccess(self, tp):
        if Access.Get(aid=self.rowid, type=Access.ROOT):
            return True
        return bool(Access.Get(aid=self.rowid, type=tp))

class Item(DBObject):
    __TABLE__ = 'items'
    __FIELDS__ = ('name', 'barcode', 'cost', 'amt')
    __DEFAULTS__ = {'barcode': None, 'amt': 0}

class Transaction(DBObject):
    __TABLE__ = 'transactions'
    __FIELDS__ = ('aid', 'iid', 'amt', 'credit', 'time')
    __DEFAULTS__ = {}

class Session(DBObject):
    __TABLE__ = 'sessions'
    __FIELDS__ = ('cookie', 'aid')
    __DEFAULTS__ = {'aid': None}
    @staticmethod
    def NewCookie():
        return str(uuid.uuid4())
