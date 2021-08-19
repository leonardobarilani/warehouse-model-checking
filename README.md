Model Checking of Warehouse Robotics
====================================

This repo contains the final project for the Computer Science and Engineering
Master's Degree course [*Formal Methods for Concurrent and Real-Time Systems*
(088882 - A.Y. 2020/21)][course] of Politecnico di Milano. The goal of the
project is to model the core entities of an automated warehouse and verify its
efficiency through the [UPPAAL][uppaal] modeling tool.

Both the [project assignment](doc/assignment.pdf) and the
[final report document](doc/report.pdf) submitted for validation can be found in
the [`doc/`](doc) folder.

Authors: [Leonardo Barilani][author-1], [Marco Bonelli][author-2].

Source code
-----------

The source code of the UPPAAL project (directly loadable into UPPAAL) submitted
for validation can be found in the file [`src/project.xml`](src/project.xml). It
includes the parameters for two main scenarios (described in the final report
document) and the queries ran for model verification. *Note: queries for
expected values take a moderately long time to run (several minutes)*.

The source code and all the assets for the final report (built using
[Pandoc][pandoc] and `pdflatex`) can be found in the [`report/`](report) folder.
Building is done through `docker-compose`:

	docker-compose run --rm build

Multi-parameter analysis
------------------------

We wrote an ad-hoc test-suite ([`src/simulation/sim.py`](src/simulation/sim.py))
to run batches of simulations varying up to 3 independent system parameters at a
time using the `verifyta` command-line tool provided by UPPAAL. The tool is
written in Python 3 to run multiple verifications in parallel (one task per CPU
core), automatically caching the simulation results and generating 4D plots
using [Matplotlib][matplotlib]. The tool was tested and should be working on
both Linux and Windows.

To produce the same 4D plots as the ones described in the final report document,
install the needed dependencies through Pip (requires Python >= 3.6):

	cd src/simulation
	python3 -m pip install -r requirements.txt

Then simply run the `sim.py` script from inside the `src/simulation` folder; the
output will be in `src/simulation/out`. Run with `-h` for information about
accepted command line options.

	./sim.py --verifyta "/path/to/verifyta"

**NOTE**: running these simulations takes quite some time as the number of
different system configurations to be tested is rather large (about 2 hours
total with 20 workwes on a Intel i9-10900 CPU @ 4.50GHz). Increasing the
probability uncertainty (`--epsilon`) or reducing the verification upper time
bound (`--tau`) decreases runtime at the cost of the accuracy of the results.

---

*Copyright &copy; 2021 Leonardo Barilani & Marco Bonelli. Licensed under the Apache License 2.0.*

[course]: https://www4.ceda.polimi.it/manifesti/manifesti/controller/ManifestoPublic.do?EVN_DETTAGLIO_RIGA_MANIFESTO=evento&aa=2020&k_cf=225&k_corso_la=481&k_indir=T2A&codDescr=088882&lang=IT&semestre=2&idGruppo=4151&idRiga=253825
[author-1]: https://github.com/leonardobarilani
[author-2]: https://github.com/mebeim
[pandoc]: https://pandoc.org
[uppaal]: https://uppaal.org
[matplotlib]: https://matplotlib.org/
