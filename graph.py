#/usr/bin/env python3

from pyx import canvas, path, color, graph, style
from io import BytesIO as StringIO
import time

import fsudb

ISO_TIME='%Y-%m-%dT%H:%M:%S'

# http://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
# Thanks, Mark and Alex!
def tex_escape(text):
	"""
		:param text: a plain text message
		:return: the message escaped to appear correctly in LaTeX
	"""
	conv = {
		'&': r'\&',
		'%': r'',
		'$': r'\$',
		'#': r'\#',
		'_': r'\_',
		'~': r'\textasciitilde{}',
		'^': r'\^{}',
		'<': r'\textless',
		'>': r'\textgreater',
	}
	text = text.replace('\\', r'\char`\\')  # First, because this is an escape...
	text = text.replace('{', r'\char`\{')  # Second, because these are grouping characters...
	text = text.replace('}', r'\char`\}')
	for k, v in conv.items():
		text = text.replace(k, v)
	for char in set([char for char in text if ord(char) > 127]):
		text = text.replace(char, '\\char"%x'%(ord(char),))
	return text

class graph_axis_time:
	__implements__ = graph.axis.texter._Itexter

	def labels(self, ticks):
		for tick in ticks:
			if tick.label is None and tick.labellevel is not None:
				tick.label = time.strftime(ISO_TIME, time.localtime(tick.num / tick.denom))

def clamp(x, l, h):
	if x is None:
		return 0
	if isinstance(x, str):
		raise TypeError('Wtf? x = %r'%(x,))
	return max(min(x, h), l)

PARAM_TYPES = {
	'width': float,
	'only_current': bool,
	'plot_current': bool,
	'min': float,
	'max': float,
}
def render(logset, width=100, only_current=True, plot_current=True, plot_zero=True, low=-500, high=500, before='', since='', accounts=''):
	all_accts = fsudb.Account.All()
	if accounts:
		aids = [int(i) for i in accounts.split(',')]
		logset = [i for i in logset if i[2] in aids]
	if since:
		since = time.mktime(time.strptime(since, ISO_TIME))
		logset = [i for i in logset if i[0] >= since]
	if before:
		before = time.mktime(time.strptime(before, ISO_TIME))
		logset = [i for i in logset if i[0] <= before]
	if plot_current:
		for acct in all_accts:
			values = [i[5] for i in logset if i[2] == acct.aid]
			if not values:
				continue
			lastval = values[-1]
			if isinstance(lastval, str):
				lastval = 0  # WTF
			logset.append([time.time(), 'renderer', acct.aid, 'balance', lastval, acct.balance, 'TEMPORARY entry to plot correctly'])
	series = []
	accts = set([i[2] for i in logset if i[3] == 'balance'])
	if only_current:
		accts -= set([i[2] for i in logset if i[3] == 'aid' and i[5] is None])
	for acct in sorted(list(accts)):
		names = [i.name for i in all_accts if i.aid == acct]
		if names:
			name = names[-1]
		else:
			name = ''
		points = []
		for entry in logset:
			if entry[2] != acct or entry[3] != 'balance':
				continue
			if isinstance(entry[4], str) or isinstance(entry[5], str):
				raise TypeError('WTF? %r'%(entry,))
			points.extend([(entry[0], clamp(entry[4], low, high)), (entry[0], clamp(entry[5], low, high))])
		series.append(graph.data.points(points, x=1, y=2, title=('Account %d (%s)'%(acct, tex_escape(name)))))
	g = graph.graphxy(width=width, x=graph.axis.lin(texter=graph_axis_time()), key=graph.key.key(pos='br', dist=0.1))
	g.plot(series, [graph.style.line([style.linestyle.solid, color.gradient.Rainbow])])
	if plot_current:
		all_values = [i[4] for i in logset if i[3] == 'balance' and i[4] is not None] + [i[5] for i in logset if i[3] == 'balance' and i[5] is not None]
		actual_min = max(min(all_values), low)
		actual_max = min(max(all_values), high)
		g.plot(graph.data.values(x=[time.time(), time.time()], y=[actual_min, actual_max], title=time.strftime(ISO_TIME)), [graph.style.line()])
	if plot_zero:
		all_times = [i[0] for i in logset if i[3] == 'balance' and i[0] is not None]
		actual_min = min(all_times)
		actual_max = max(all_times)
		g.plot(graph.data.values(x=[actual_min, actual_max], y=[0.0, 0.0], title='Y=0.0'), [graph.style.line()])
	output = StringIO()
	g.writeSVGfile(output)
	return output

if __name__ == '__main__':
	import fsudb, sys, json
	options = json.load(sys.stdin)
	for k, t in PARAM_TYPES.items():
		if k in options:
			options[k] = t(options[k])
	sys.stdout.write(render(fsudb.Log.All(), **options).getvalue().decode('utf8'))
