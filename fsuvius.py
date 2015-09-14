from flask import Flask, request, g, render_template, make_response
from flask.json import jsonify
import json
import pprint
import socket
import struct

from fsudb import Account, Log

def aton(h):
	return struct.unpack('>I', socket.inet_aton(h))[0]

def ntoa(i):
	return socket.inet_ntoa(struct.pack('>I', i))

ALLOWED_SUBNET = aton('128.153.144.0')
ALLOWED_MASK = aton('255.255.254.0')

app = Flask('fsuvius')
app.debug = True

class ERR:
	UNKNOWN=0
	NEXIST=1
	EXIST=2
	DOMAIN=3
	ACCESS=4

def as_acctobj(acct):
	return {'aid': acct.aid, 'name': acct.name, 'balance': acct.balance}

@app.route('/')
def root():
	return render_template('root.html')

def check_priv():
	host = aton(request.environ['REMOTE_ADDR'])
	if request.method == 'POST' and ALLOWED_SUBNET != (ALLOWED_MASK & host):
		return jsonify(error={'code': ERR.ACCESS, 'reason': 'Modification not allowed from outside the %s subnet'%(ntoa(ALLOWED_SUBNET),)})

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
