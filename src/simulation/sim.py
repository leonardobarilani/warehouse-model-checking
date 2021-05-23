#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import pickle
from multiprocessing import Pool
from itertools import product
import tempfile
import signal

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
from tqdm import tqdm

def handle_sigint(*_):
	sys.exit(0)

def eprint(*a, **kwa):
	print(*a, **kwa, file=sys.stderr)

def format_params(params, variable_params):
	with open('template.xml') as f:
		proj = f.read()

	pp = params.copy()

	if 'TASK_GEN_VAR_PERCENT' in variable_params:
		variable_params['TASK_GEN_VAR'] = int(variable_params['TASK_GEN_MEAN'] * variable_params['TASK_GEN_VAR_PERCENT'])

	pp.update(variable_params)
	assert pp['N_BOTS'] + pp['QUEUE_CAPACITY'] < pp['N_POD_ROWS'] * pp['N_PODS_PER_ROW']

	return proj.format(**pp)

def run_query(qpp):
	signal.signal(signal.SIGINT, handle_sigint)
	query, params, variable_params = qpp

	query_fd, query_fname = tempfile.mkstemp(suffix='.txt')
	os.write(query_fd, query.encode())
	os.close(query_fd)

	proj_fd, proj_fname = tempfile.mkstemp(suffix='.xml')
	os.write(proj_fd, format_params(params, variable_params).encode())
	os.close(proj_fd)

	cmd = [
		VERIFYTA_EXE_PATH,
		'-C',
		'-S', '0',
		'-H', '32',
		'-E', VERIFYTA_UNCERTAINTY,
		proj_fname,
		query_fname
	]

	res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	os.remove(query_fname)
	os.remove(proj_fname)

	if res.returncode != 0:
		eprint('[ERROR]', res.stderr.decode().rstrip())
		sys.exit(1)

	out = res.stdout.decode()
	assert 'Formula is satisfied' in out

	matches = VERIFYTA_REGEX.findall(out)

	if not matches:
		eprint('[ERROR] Regexp matching failed:')
		eprint('[ERROR] ' + '\n[ERROR] '.join(res.stdout.decode().splitlines()))
		sys.exit(1)

	return variable_params, tuple(map(float, matches[0][1:]))

def gen_args(query, params, ranges):
	ks = tuple(ranges.keys())
	ranges = tuple(map(ranges.get, ks))

	for vs in product(*ranges):
		variable_params = {k:v for k, v in zip(ks, vs)}
		yield query, params, variable_params

def run_multi(query, params, ranges, xyz):
	xk, yk, zk = xyz
	xs, ys, zs, cs = [], [], [], []

	p = Pool(N_WORKERS)
	args = list(gen_args(query, params, ranges))
	total = len(args)

	eprint(f'Query: {query}')
	eprint(f'Spawning {N_WORKERS} workers to run {total} simulations.')

	for res in tqdm(p.imap_unordered(run_query, args), desc='Simulating', total=total):
		if res is None:
			sys.exit(1)

		variable_params, p = res
		# tqdm.write(f'{variable_params!r} -> {p!r}')

		xs.append(variable_params[xk])
		ys.append(variable_params[yk])
		zs.append(variable_params[zk])
		cs.append((p[0] + p[1]) / 2)

	return xs, ys, zs, cs

def gen_plot(x, y, z, v, labels, ticks, fname, view_init):
	plt.rcParams.update({
		'font.size': 8,
		'figure.figsize': (9, 6),
		'figure.autolayout': True,
	})

	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d', proj_type='ortho')

	# set azimuth and elevation for image orientation
	ax.view_init(*view_init)

	mx, Mx = min(x), max(x)
	my, My = min(y), max(y)
	mz, Mz = min(z), max(z)
	patches = []

	for zv in set(z):
		patches.append([[mx, my, zv], [mx, My, zv], [Mx, My, zv], [Mx, my, zv]])

	pc = Poly3DCollection(patches)
	pc.set_facecolor((0, 0, 0, 0.1))
	ax.add_collection3d(pc)

	# for whatever reason this needs to be explicitly set
	ax.set_xlim(mx, Mx)
	ax.set_ylim(my, My)
	ax.set_zlim(mz, Mz)

	img = ax.scatter(x, y, z, c=v, cmap=COLOR_MAP, s=8, alpha=1)

	# make the panes transparent
	ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
	ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
	ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

	# make the grid lines transparent
	ax.xaxis._axinfo["grid"]['color'] =  (1,1,1,0)
	ax.yaxis._axinfo["grid"]['color'] =  (1,1,1,0)
	ax.zaxis._axinfo["grid"]['color'] =  (1,1,1,0)

	# color legend
	cbar = fig.colorbar(img, shrink=0.5, ticks=[min(v), 0.5, max(v)])

	# axis labels
	ax.set_xlabel(labels[0])
	ax.set_ylabel(labels[1])
	ax.set_zlabel(labels[2])

	# axis ticks
	ax.xaxis.set_ticks(ticks[0])
	ax.yaxis.set_ticks(ticks[1])
	ax.zaxis.set_ticks(ticks[2])

	if 'show' in sys.argv:
		plt.show()

	plt.savefig(fname, pad_inches=0)

def g1():
	params = DEFAULT_PARAMS.copy()

	varparams = {
		'TASK_GEN_MEAN': range(10, 20 + 1),
		'TASK_GEN_VAR_PERCENT': map(lambda x: x * 0.01, range(0, 100 + 1, 10)),
		'QUEUE_CAPACITY': [1,] + list(range(5, 30 + 1, 5))
	}

	for k, v in varparams.items():
		if type(v) is not list:
			varparams[k] = list(v)

	keys = ['TASK_GEN_MEAN', 'TASK_GEN_VAR_PERCENT', 'QUEUE_CAPACITY']
	labels = ['task gen mean time', 'task gen variance%', 'queue capacity']
	data = None

	if 'gen' not in sys.argv:
		try:
			with open('mean_var_qsize.pkl', 'rb') as f:
				data = pickle.load(f)
		except:
			pass

	if data is None:
		data = run_multi('Pr [<=1000] ( <> tasks_lost > 0 )', params, varparams, keys)

	with open('mean_var_qsize.pkl', 'wb') as f:
		pickle.dump(data, f)

	ticks = [
		varparams['TASK_GEN_MEAN'],
		[0.0, 0.5, 1.0],
		varparams['QUEUE_CAPACITY']
	]

	gen_plot(*data, labels, ticks, 'plot3d_mean_var_qsize.png', (5, -81))

def g2():
	params = DEFAULT_PARAMS.copy()

	varparams = {
		'TASK_GEN_MEAN': range(10, 20 + 1),
		'N_BOTS': range(1, 11),
		'QUEUE_CAPACITY': [1,] + list(range(5, 25 + 1, 5))
	}

	for k, v in varparams.items():
		if type(v) is not list:
			varparams[k] = list(v)

	keys = ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_BOTS']
	labels = ['task gen mean time', 'queue capacity', 'n bots']
	data = None

	if 'gen' not in sys.argv:
		try:
			with open('mean_nbots_qsize.pkl', 'rb') as f:
				data = pickle.load(f)
		except:
			pass

	if data is None:
		data = run_multi('Pr [<=1000] ( <> tasks_lost > 0 )', params, varparams, keys)

	with open('mean_nbots_qsize.pkl', 'wb') as f:
		pickle.dump(data, f)

	ticks = [
		varparams['TASK_GEN_MEAN'],
		[1, 5, 15, 25],
		varparams['N_BOTS'],
	]

	gen_plot(*data, labels, ticks, 'plot3d_mean_nbots_qsize.png', (3, -86))

################################################################################

# inverted
COLOR_DICT = {
	'red'  : ((0.0, 0.0, 0.0), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.9, 0.9)),
	'green': ((0.0, 0.9, 0.9), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.0, 0.0)),
	'blue' : ((0.0, 0.0, 0.0),                                   (1.0, 0.1, 0.1))
}

COLOR_MAP = mcolors.LinearSegmentedColormap('gyr', COLOR_DICT, 100)

DEFAULT_PARAMS = {
	'N_BOTS'           : 5,
	'N_POD_ROWS'       : 10,
	'N_PODS_PER_ROW'   : 5,
	'TASK_GEN_MEAN'    : 1,
	'TASK_GEN_VAR'     : 0,
	'QUEUE_CAPACITY'   : 10,
	'HUMAN_MEAN'       : 2,
	'HUMAN_VAR'        : 1,
	'BOT_IDLE_EXP_RATE': 10,
	'BOT_STEP_TIME'    : 1,
	'TAU'              : 1000,
}

N_WORKERS            = os.cpu_count()
VERIFYTA_EXE_PATH    = '/home/marco/Downloads/Chrome/uppaal64-4.1.24/bin-Linux/verifyta'
VERIFYTA_REGEX       = re.compile(r'Pr\((<>|\[\]) \.\.\.\) in \[([\d.e-]+),([\d.e-]+)\]')
VERIFYTA_UNCERTAINTY = '0.1'

################################################################################

if __name__ == '__main__':
	signal.signal(signal.SIGINT, handle_sigint)
	g1()
	g2()