from flask import Flask, request, g, render_template, make_response
from flask.json import jsonify
import json
import pprint
import socket
import struct

from fsudb import Access, Account, Item, Transaction, Session
from changes import Changes

class ERR:
    UNKNOWN=0
    NEXIST=1
    EXIST=2
    DOMAIN=3
    ACCESS=4

class Network(object):
    def __init__(self, netip, netmask):
        self.netip = aton(netip)
        self.netmask = aton(netmask)

    def __contains__(self, val):
        return aton(val) & self.netmask == self.netip

ALLOWED_NETWORKS = [
    Network('128.153.144.0', '255.255.254.0'),
    Network('10.0.0.0', '255.0.0.0'),
]

def check_priv():
    host = request.environ['REMOTE_ADDR']
    for net in ALLOWED_NETWORKS:
        if host in net:
            return None
    return jsonify(error={'code': ERR.ACCESS, 'reason': 'Not in an allowed subnet'})

app = Flask('fsuvius')
app.debug = True
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


def as_acctobj(acct):
    return {'aid': acct.rowid, 'name': acct.name, 'dispname', acct.dispname, 'balance': acct.balance}

def as_change(type, acct):
    return {'type': type, 'acct': as_acctobj(acct)}

@app.route('/')
def root():
    return render_template('root.jade')

@app.route('/transact', methods=['POST', 'GET'])
def transact():
    resp = check_priv()
    if resp is not None:
        return resp
    try:
        acct = Account.GetOne(rowid=request.values.get('aid', -1, type=int))
    except DBError:
        return jsonify(error={'code': ERR.NEXIST, 'reason': 'Bad account ID'})
    try:
        item = Item.GetOne(rowid=request.values.get('iid', -1, type=int))
    except DBError:
        return jsonify(error={'code': ERR.NEXIST, 'reason': 'Bad item ID'})
    amt = request.values.get('amt', 1, type=int)
    credit = request.values.get('credit'
    Transaction.Create(acct.rowid, item.iid, 

@app.route('/mod', methods=['POST', 'GET'])
@app.route('/set', methods=['POST', 'GET'])
def mod_set():
	resp = check_priv()
	if resp is not None:
		return resp
	try:
		acct = Account.FromID(request.values['aid'])
	except DBError:
		return jsonify(error={'code': ERR.NEXIST, 'reason': 'Bad user ID'})
	try:
		amt = float(request.values['amt'])
	except ValueError:
		return jsonify(error={'code': ERR.DOMAIN, 'reason': 'Amt not a number'})
	if request.values.get('set', False) or request.path == '/set':
		acct.balance = amt
	elif request.path == '/mod':
		if request.values.get('dock', False):
			amt = -amt
		acct.balance += amt
	else:
		return jsonify(error={'code': ERR.DOMAIN, 'reason': 'Not a mod or set request (path was %s)'%(request.path,)})
	acct.Update(src = request.environ['REMOTE_ADDR'])
	return jsonify(accounts=[as_acctobj(acct)])

@app.route('/mv', methods=['POST', 'GET'])
def mv():
	# return jsonify(error={'code': ERR.ACCESS, 'reason': 'Modification to this field is not allowed'})
	resp = check_priv()
	if resp is not None:
		return resp
	try:
		acct = Account.FromID(request.values['aid'])
	except DBError:
		return jsonify(error={'code': ERR.NEXIST, 'reason': 'Bad user ID'})
	acct.name = request.values['name']
	acct.Update(src = request.environ['REMOTE_ADDR'])
	return jsonify(accoutns=[as_acctobj(acct)])

@app.route('/new', methods=['POST', 'GET'])
def new():
	resp = check_priv()
	if resp is not None:
		return resp
	acct = Account.Create(request.values['name'], 0, src = request.environ['REMOTE_ADDR'])
	return jsonify(accounts=[as_acctobj(acct)])

@app.route('/get', methods=['POST', 'GET'])
def get():
	accts = Account.All()
	return jsonify(accounts=[as_acctobj(i) for i in accts])

@app.route('/dbg/req', methods=['GET', 'POST'])
def dbg_req():
	resp = make_response('%s\n%s'%(pprint.pformat(request), pprint.pformat(request.environ)))
	resp.mimetype = 'text/plain'
	return resp

@app.route('/dbg/log', methods=['GET'])
def dbg_log():
	resp = make_response('\n'.join([i[6] for i in Log.All()]))
	resp.mimetype = 'text/plain'
	return resp

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
