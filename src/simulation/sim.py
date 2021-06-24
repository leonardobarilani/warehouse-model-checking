#!/usr/bin/env python3
#
# Given a project XML template, run different simulations in parallel on all
# available CPUs varying 3 different parameters. Results are cached into the
# 'out/' folder (created if not existing). Plots are then generated from those
# results and saved them in the same folder as PNG images.
#
# ./sim.py template.xml [gen] [show]
#
#   gen : force re-simulation even if cache is present (otherwise only generates
#         the plot based on the last simulation)
#   show: show interactive plot instead of saving to file
#

import os
import sys
import re
import subprocess
import pickle
from multiprocessing import Pool
from itertools import product
import tempfile
import signal

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
from tqdm import tqdm

def handle_sigint(*_):
	sys.stderr.close()
	sys.exit(0)

def eprint(*a, **kwa):
	print(*a, **kwa, file=sys.stderr)

def format_params(params, variable_params):
	with open(TEMPLATE_FNAME) as f:
		proj = f.read()

	pp = params.copy()

	if 'N_PODS_PER_ROW_E' in variable_params:
		variable_params['N_PODS_PER_ROW_W'] = 10 - variable_params['N_PODS_PER_ROW_E'];

	pp.update(variable_params)
	assert pp['N_BOTS'] + pp['QUEUE_CAPACITY'] < pp['N_POD_ROWS'] * (pp['N_PODS_PER_ROW_E'] + pp['N_PODS_PER_ROW_W'])

	return proj.format(**pp)

def run_query(qpp):
	query, params, variable_params = qpp

	proj_file = tempfile.NamedTemporaryFile('w+', suffix='.xml')
	proj_file.write(format_params(params, variable_params))
	proj_file.seek(0)

	query_file = tempfile.NamedTemporaryFile('w+', suffix='.txt')
	query_file.write(query)
	query_file.seek(0)

	cmd = [
		VERIFYTA_EXE_PATH,
		'-C',
		'-S', '0',
		'-H', '32',
		'-E', VERIFYTA_UNCERTAINTY,
		proj_file.name,
		query_file.name
	]

	res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proj_file.close()
	query_file.close()

	if res.returncode != 0:
		eprint('[ERROR]', res.stderr.decode().rstrip())
		sys.exit(1)

	out = res.stdout.decode()

	if 'Formula is satisfied' not in out:
		eprint('[ERROR] Formula not satisfied?')
		eprint('[ERROR] ' + '\n[ERROR] '.join(out.splitlines()))
		assert False

	matches = VERIFYTA_REGEX.findall(out)

	if not matches:
		eprint('[ERROR] Regexp matching failed:')
		eprint('[ERROR] ' + '\n[ERROR] '.join(out.splitlines()))
		assert False

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
	eprint(f'Uncertainty: {VERIFYTA_UNCERTAINTY}')
	eprint('Variable params:')

	for k, v in ranges.items():
		eprint(f'  - {k}: {v!r}')

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
	else:
		plt.savefig(fname, pad_inches=0)

def sim1():
	params = DEFAULT_PARAMS.copy()
	params.update({
		'N_BOTS'    : 5,
		'N_POD_ROWS': 5,
	})

	varparams = {
		'TASK_GEN_MEAN'   : range(10, 20 + 1),
		'QUEUE_CAPACITY'  : [1,] + list(range(5, 20 + 1, 5)),
		'N_PODS_PER_ROW_E': range(0, 10 + 1)
	}

	for k, v in varparams.items():
		if type(v) is not list:
			varparams[k] = list(v)

	keys = ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_PODS_PER_ROW_E']
	labels = ['task gen mean time', 'queue capacity', 'pods per row (east)']
	data = None

	if 'gen' not in sys.argv:
		try:
			with open(f'{OUT_FNAME_PREFIX}_gen_highway_qsize.pkl', 'rb') as f:
				data = pickle.load(f)
		except:
			pass

	if data is None:
		data = run_multi('Pr [<=TAU] ( <> tasks_lost > 0 )', params, varparams, keys)

	with open(f'{OUT_FNAME_PREFIX}_gen_highway_qsize.pkl', 'wb') as f:
		pickle.dump(data, f)

	ticks = [
		varparams['TASK_GEN_MEAN'],
		varparams['QUEUE_CAPACITY'],
		varparams['N_PODS_PER_ROW_E'],
	]

	gen_plot(*data, labels, ticks, f'{OUT_FNAME_PREFIX}_plot3d_gen_highway_qsize.png', (4, -84))

def sim2():
	params = DEFAULT_PARAMS.copy()

	varparams = {
		'TASK_GEN_MEAN': range(10, 20 + 1),
		'N_BOTS': range(1, 10 + 1),
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
			with open(f'{OUT_FNAME_PREFIX}_mean_nbots_qsize.pkl', 'rb') as f:
				data = pickle.load(f)
		except:
			pass

	if data is None:
		data = run_multi('Pr [<=TAU] ( <> tasks_lost > 0 )', params, varparams, keys)

	with open(f'{OUT_FNAME_PREFIX}_mean_nbots_qsize.pkl', 'wb') as f:
		pickle.dump(data, f)

	ticks = [
		varparams['TASK_GEN_MEAN'],
		[1, 5, 15, 25],
		varparams['N_BOTS'],
	]

	gen_plot(*data, labels, ticks, f'{OUT_FNAME_PREFIX}_plot3d_mean_nbots_qsize.png', (3, -86))

def main():
	global TEMPLATE_FNAME
	global OUT_FNAME_PREFIX

	signal.signal(signal.SIGINT, handle_sigint)
	os.makedirs('out', exist_ok=True)

	for a in sys.argv:
		if a.endswith('.xml'):
			TEMPLATE_FNAME = a

	if TEMPLATE_FNAME is None:
		eprint('Usage: ./sim.py template.xml [gen] [show]')
		sys.exit(1)

	OUT_FNAME_PREFIX = os.path.join('out', TEMPLATE_FNAME[:-4])

	sim1()
	#sim2()

################################################################################

# inverted
COLOR_DICT = {
	'red'  : ((0.0, 0.0, 0.0), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.9, 0.9)),
	'green': ((0.0, 0.9, 0.9), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.0, 0.0)),
	'blue' : ((0.0, 0.0, 0.0),                                     (1.0, 0.1, 0.1))
}

COLOR_MAP = mcolors.LinearSegmentedColormap('gyr', COLOR_DICT, 100)

DEFAULT_PARAMS = {
	'N_BOTS'           : 5,
	'N_POD_ROWS'       : 5,
	'N_PODS_PER_ROW_W' : 3,
	'N_PODS_PER_ROW_E' : 3,
	'QUEUE_CAPACITY'   : 10,
	'TASK_GEN_MEAN'    : 1,
	'TASK_GEN_VAR'     : 0,
	'HUMAN_MEAN'       : 2,
	'HUMAN_VAR'        : 1,
	'BOT_IDLE_EXP_RATE': 3,
	'BOT_STEP_TIME'    : 1,
	'TAU'              : 1000,
}

TEMPLATE_FNAME       = './template.xml'
OUT_FNAME_PREFIX     = None
N_WORKERS            = os.cpu_count()
VERIFYTA_EXE_PATH    = '/home/marco/Downloads/Chrome/uppaal64-4.1.24/bin-Linux/verifyta'
VERIFYTA_REGEX       = re.compile(r'Pr\((<>|\[\]) \.\.\.\) in \[([\d.e-]+),([\d.e-]+)\]')
VERIFYTA_UNCERTAINTY = '0.01'

################################################################################

if __name__ == '__main__':
	main()
