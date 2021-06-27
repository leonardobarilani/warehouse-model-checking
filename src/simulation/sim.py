#!/usr/bin/env python3
#
# Given a project XML template, run different simulations in parallel on all
# available CPUs varying 3 different parameters. Results are cached into the
# 'out/' folder (created if not existing). Plots are then generated from those
# results and saved in the same folder as PNG images.
#
# usage: sim.py [-h] [-s] [-r] [-f FILTER] [-e E] [-t TAU] [-v VERIFYTA_PATH]
#               [TEMPLATE.xml]
#
# positional arguments:
#   TEMPLATE.xml          project template to use for simulation (default:
#                         ./template.xml)
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -s, --show            show interactive plot instead of generating PNGs
#                         (default: False)
#   -r, --rerun           force re-running simulations overwriting already
#                         cached results (default: False)
#   -f FILTER, --filter FILTER
#                         only run simulations whose name (partially) matches
#                         the filter (default: None)
#   -e E, --epsilon E     verifyta probability accuracy (epsilon) (default:
#                         0.05)
#   -t TAU, --tau TAU     simulation upper time bound (default: 10000)
#   -v VERIFYTA_PATH, --verifyta VERIFYTA_PATH
#                         path to verifyta executable (default: ./uppaal/bin-
#                         Linux/verifyta)

import os
import sys
import re
import subprocess
import pickle
import argparse
from multiprocessing import Pool
from itertools import product
import tempfile
import signal
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
from tqdm import tqdm


def handle_sigint(*_):
	sys.stderr.close()
	sys.exit(0)


def eprint(*a, **kwa):
	print(*a, **kwa, file=sys.stderr)


def get_args():
	ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	ap.add_argument('-s', '--show', action='store_true', help='show interactive plot instead of generating PNGs')
	ap.add_argument('-r', '--rerun', action='store_true', help='force re-running simulations overwriting already cached results')
	ap.add_argument('-f', '--filter', type=str, metavar='FILTER', default=None, help='only run simulations whose name (partially) matches the filter')
	ap.add_argument('-e', '--epsilon', type=float, metavar='E', default=0.01, help='verifyta probability accuracy (epsilon)')
	ap.add_argument('-t', '--tau', type=int, metavar='TAU', default=10000, help='simulation upper time bound')
	ap.add_argument('-v', '--verifyta', type=str, metavar='VERIFYTA_PATH', default='./uppaal/bin-Linux/verifyta', help='path to verifyta executable')
	ap.add_argument('template_fname', nargs='?', metavar='TEMPLATE.xml', default='./template.xml', help='project template to use for simulation')
	return ap.parse_args()


def format_params(params, variable_params):
	with open(TEMPLATE_FNAME) as f:
		proj = f.read()

	pp = params.copy()
	pp.update(variable_params)
	assert pp['N_BOTS'] + pp['QUEUE_CAPACITY'] < pp['N_POD_ROWS'] * (pp['N_PODS_PER_ROW_W'] + pp['N_PODS_PER_ROW_E'])

	return proj.format(**pp)


def run_query(qpp):
	query, params, variable_params = qpp

	proj_file = tempfile.NamedTemporaryFile('w+', prefix='whsim_', suffix='.xml')
	proj_file.write(format_params(params, variable_params))
	proj_file.seek(0)

	query_file = tempfile.NamedTemporaryFile('w+', prefix='whsim_', suffix='.txt')
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

	if res.returncode != 0:
		eprint('[ERROR]', res.stderr.decode().rstrip())

		proj_file.seek(0)
		with open('/tmp/whsim_err.xml', 'w') as f:
			f.write(proj_file.read())

		sys.exit(1)

	proj_file.close()
	query_file.close()

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


def gen_args(query, params, varparams, funcparams):
	ks = tuple(varparams.keys())
	varparams = tuple(map(varparams.get, ks))

	for vs in product(*varparams):
		variable_params = {k:v for k, v in zip(ks, vs)}

		for k, f in funcparams.items():
			variable_params[k] = f(variable_params)

		yield query, params, variable_params


def run_multi(query, params, varparams, funcparams, xyz):
	xk, yk, zk = xyz
	xs, ys, zs, cs = [], [], [], []

	p = Pool(N_WORKERS)
	args = list(gen_args(query, params, varparams, funcparams))
	total = len(args)

	eprint(f'Query: {query}')
	eprint(f'Uncertainty: {VERIFYTA_UNCERTAINTY}')

	eprint('Fixed params:')
	for k, v in params.items():
		eprint(f'  - {k}: {v!r}')

	eprint('Variable params:')
	for k, v in varparams.items():
		eprint(f'  - {k}: {v!r}')

	eprint('Functional params: ' + ' '.join(funcparams.keys()))
	eprint(f'\nSpawning {N_WORKERS} workers to run {total} simulations.')

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
		'font.size': 10,
		'figure.figsize': (10, 8),
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

	img = ax.scatter(x, y, z, c=v, cmap=COLOR_MAP, s=12, alpha=1)

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
	ax.set_xlabel(labels[0], fontsize=10, labelpad=10)
	ax.set_ylabel(labels[1], fontsize=10, labelpad=5)
	ax.set_zlabel(labels[2], fontsize=10, labelpad=10)

	# axis ticks
	for t, axis in zip(ticks, (ax.xaxis, ax.yaxis, ax.zaxis)):
		axis.set_ticks(t)

	if SHOW:
		plt.show()
	else:
		plt.savefig(fname, pad_inches=0)
		print('Plot saved to', fname)


def simulate(name, params, varparams, funcparams, keys, labels, ticks, plot_view_init):
	params['TAU'] = TAU

	for k, v in varparams.items():
		if type(v) is not list and not callable(v):
			varparams[k] = list(v)

	data = None
	data_fname = f'{OUT_DIR}/{name}.pkl'
	plot_fname = f'{OUT_DIR}/{name}.png'

	if not RERUN:
		try:
			with open(data_fname, 'rb') as f:
				data = pickle.load(f)
		except:
			pass

	if data is None:
		data = run_multi(QUERY, params, varparams, funcparams, keys)

		with open(data_fname, 'wb') as f:
			pickle.dump(data, f)
	else:
		eprint('Simulation result already present, run with -r to overwrite')

	for i, t in enumerate(ticks):
		if t == 'all':
			ticks[i] = varparams[keys[i]]

	gen_plot(*data, labels, ticks, plot_fname, plot_view_init)


def main():
	global TEMPLATE_FNAME
	global TAU
	global VERIFYTA_UNCERTAINTY
	global RERUN
	global SHOW
	global VERIFYTA_EXE_PATH

	signal.signal(signal.SIGINT, handle_sigint)
	os.makedirs(OUT_DIR, exist_ok=True)

	args                 = get_args()
	TEMPLATE_FNAME       = args.template_fname
	TAU                  = args.tau
	VERIFYTA_UNCERTAINTY = str(args.epsilon)
	RERUN                = args.rerun
	SHOW                 = args.show
	VERIFYTA_EXE_PATH    = args.verifyta

	for name, params in SIMULATIONS.items():
		if not args.filter or args.filter in name:
			eprint('RUNNING SIMULATION', name)
			simulate(name, **params)

################################################################################

# inverted
COLOR_DICT = {
	'red'  : ((0.0, 0.0, 0.0), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.9, 0.9)),
	'green': ((0.0, 0.9, 0.9), (0.45, 0.9, 0.9), (0.55, 0.9, 0.9), (1.0, 0.0, 0.0)),
	'blue' : ((0.0, 0.0, 0.0),                                     (1.0, 0.1, 0.1))
}

COLOR_MAP = mcolors.LinearSegmentedColormap('gyr', COLOR_DICT, 100)

OUT_DIR           = 'out'
N_WORKERS         = os.cpu_count()
VERIFYTA_REGEX    = re.compile(r'Pr\((<>|\[\]) \.\.\.\) in \[([\d.e-]+),([\d.e-]+)\]')
QUERY             = 'Pr [<=TAU] (<> tasks_lost > 0)'

SIMULATIONS = {
	'01_highway_placement': {
		'params': {
			'N_BOTS'           : 5,
			'N_POD_ROWS'       : 5,
			'TASK_GEN_VAR'     : 1,
			'HUMAN_MEAN'       : 2,
			'HUMAN_VAR'        : 5,
			'BOT_IDLE_EXP_RATE': 3,
			'BOT_STEP_TIME'    : 1,
		},
		'varparams': {
			'TASK_GEN_MEAN'   : range(10, 20 + 1),
			'QUEUE_CAPACITY'  : [1,] + list(range(5, 20 + 1, 5)),
			'N_PODS_PER_ROW_W': range(0, 10 + 1)
		},
		'funcparams': {
			'N_PODS_PER_ROW_E': lambda vp: 10 - vp['N_PODS_PER_ROW_W']
		},
		'keys'  : ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_PODS_PER_ROW_W'],
		'labels': ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_PODS_PER_ROW_W\n= 10 - N_PODS_PER_ROW_E'],
		'ticks' : ['all', 'all', 'all'],
		'plot_view_init': (2.5, -86)
	},

	'02_queue_capacity': {
		'params': {
			'N_POD_ROWS'       : 5,
			'N_PODS_PER_ROW_W' : 5,
			'N_PODS_PER_ROW_E' : 5,
			'TASK_GEN_VAR'     : 5,
			'HUMAN_MEAN'       : 2,
			'HUMAN_VAR'        : 1,
			'BOT_IDLE_EXP_RATE': 3,
			'BOT_STEP_TIME'    : 1,
		},
		'varparams': {
			'TASK_GEN_MEAN' : range(5, 20 + 1),
			'N_BOTS'        : range(3, 10 + 1),
			'QUEUE_CAPACITY': range(1, 8 + 1)
		},
		'funcparams': {},
		'keys'  : ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_BOTS'],
		'labels': ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_BOTS'],
		'ticks' : ['all', [1, 5, 10], 'all',],
		'plot_view_init': (5, -83)
	},

	# '03_queue_capacity_big_warehouse': {
	# 	'params': {
	# 		'N_POD_ROWS'       : 20,
	# 		'N_PODS_PER_ROW_W' : 10,
	# 		'N_PODS_PER_ROW_E' : 10,
	# 		'TASK_GEN_VAR'     : 5,
	# 		'HUMAN_MEAN'       : 2,
	# 		'HUMAN_VAR'        : 1,
	# 		'BOT_IDLE_EXP_RATE': 3,
	# 		'BOT_STEP_TIME'    : 1,
	# 	},
	# 	'varparams': {
	# 		'TASK_GEN_MEAN' : range(10, 20 + 1),
	# 		'N_BOTS'        : range(10, 20 + 1),
	# 		'QUEUE_CAPACITY': range(10, 20 + 1)
	# 	},
	# 	'funcparams': {},
	# 	'keys'  : ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_BOTS'],
	# 	'labels': ['TASK_GEN_MEAN', 'QUEUE_CAPACITY', 'N_BOTS'],
	# 	'ticks' : ['all', 'all', [10, 12, 14, 16, 18, 20]],
	# 	'plot_view_init': (3, -86)
	# },

	# '04_warehouse_shape': {
	# 	'params': {
	# 		'QUEUE_CAPACITY'   : 15,
	# 		'TASK_GEN_MEAN'    : 10,
	# 		'TASK_GEN_VAR'     : 1,
	# 		'HUMAN_MEAN'       : 2,
	# 		'HUMAN_VAR'        : 1,
	# 		'BOT_IDLE_EXP_RATE': 3,
	# 		'BOT_STEP_TIME'    : 1,
	# 	},
	# 	'varparams': {
	# 		'N_BOTS'          : range(10, 20 + 1, 2),
	# 		'N_POD_ROWS'      : range(8, 20 + 1, 2),
	# 		'N_PODS_PER_ROW_W': range(4, 20 + 1),
	# 	},
	# 	'funcparams': {
	# 		'N_PODS_PER_ROW_E': lambda vp: vp['N_PODS_PER_ROW_W']
	# 	},
	# 	'keys'  : ['N_PODS_PER_ROW_W', 'N_BOTS', 'N_POD_ROWS'],
	# 	'labels': ['N_PODS_PER_ROW_{W,E}', 'N_BOTS', 'N_POD_ROWS'],
	# 	'ticks' : ['all', 'all', 'all'],
	# 	'plot_view_init': (4, -84)
	# },
}

################################################################################

if __name__ == '__main__':
	main()
