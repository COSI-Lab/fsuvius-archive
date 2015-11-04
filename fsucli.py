from sys import argv
from urllib2 import urlopen
from urllib import urlencode
from json import loads
from pprint import pprint

# Fsuvius CLI
# Made by Benjamin Lannon
# Minor tweaks from Alan Beadle
# Commands:
# python fsucli.py -> lists all accounts.
# python fsucli.py dock <id> <num> -> docks <num> fsu from <id>.
# python fsucli.py dock <id> -> docks 1 fsu from <id>.
# python fsucli.py add <id> <num> -> adds <num> fsu to <id>.
# python fsucli.py add <id> -> adds 1 fsu to <id>.

URL="http://fsuvius.cslabs.clarkson.edu"

class FsuviusError(Exception):
    @classmethod
    def check(cls, result):
        if 'error' in result:
            raise cls(result['error']['code'], result['error']['reason'])

def list_accounts():
    result = loads(urlopen(URL + "/get").read())
    FsuviusError.check(result)
    acct_list = result['accounts']
    hdr='{aid:<8}{name:30}{balance:10}'.format(aid='ID', name='NAME', balance='BALANCE')
    print hdr
    print '='*len(hdr)
    for acct in acct_list:
        print '{u[aid]:<8}{u[name]:30}{u[balance]:10}'.format(u=acct)

def dock_fsu(aid, num):
    result = loads(urlopen(URL + '/mod', urlencode({'aid': aid, 'amt': num, 'dock': True})).read())
    FsuviusError.check(result)
    print("docked {} fsu from ID {}").format(num, aid)
    list_accounts()

def add_fsu(aid, num):
    result = loads(urlopen(URL + '/mod', urlencode({'aid': aid, 'amt': num})).read())
    FsuviusError.check(result)
    print("added {} fsu to ID {}").format(num, aid)
    list_accounts()

def rename(aid, name):
    result = loads(urlopen(URL + '/mv', urlencode({'aid': aid, 'name': name})).read())
    FsuviusError.check(result)
    print("renamed ID {} to {}").format(aid, name)
    list_accounts()

def do_thing():
    if len(argv) == 1:
        list_accounts()
    else:
        if len(argv) == 3:
            fsu=1
        else:
            fsu=argv[3]
        if argv[1] == "dock":
            dock_fsu(argv[2], fsu)
        elif argv[1] == "add":
            add_fsu(argv[2], fsu)
        elif argv[1] == "rename":
            rename(argv[2], fsu)

if __name__ == '__main__':
    do_thing()
