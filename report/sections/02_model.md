UPPAAL Model
============

Global Declarations
-------------------

### System parameters

\bgroup
\def\arraystretch{0.8}
\begin{center}
\rowcolors{2}{gray!10}{white}
\begin{tabular}{ | l | l | }
	\hline
	\textbf{Parameter} & \textbf{Description} \\
	\hline
	\texttt{N\_BOTS}              & Number of robots in the warehouse \\
	\texttt{N\_POD\_ROWS}         & Number of rows of pods in the warehouse \\
	\texttt{N\_PODS\_PER\_ROW\_W} & Number of pods per single row on the warehouse West side \\
	\texttt{N\_PODS\_PER\_ROW\_E} & Number of pods per single row on the warehouse East side \\
	\texttt{QUEUE\_CAPACITY}      & Capacity of the tasks' queue \\
	\texttt{TASK\_GEN\_MEAN}      & Task generation mean time ($\mu_T$) \\
	\texttt{TASK\_GEN\_VAR}       & Task generation time variance ($\sigma_T$) \\
	\texttt{HUMAN\_MEAN}          & Human operator mean reaction time ($\mu_H$) \\
	\texttt{HUMAN\_VAR}           & Human operator reaction time variance ($\sigma_H$) \\
	\texttt{BOT\_IDLE\_EXP\_RATE} & Robot task claim delay ($\lambda$ of exponential distribution) \\
	\texttt{BOT\_STEP\_TIME}      & Time needed for a robot to move between adjacent tiles \\
	\texttt{ENTRY\_POS}           & Entry point position (coordinates) \\
	\texttt{HUMAN\_POS}           & Human operator position (coordinates) \\
	\texttt{TAU}                  & Upper time bound for verification \\
	\hline
\end{tabular}
\end{center}
\egroup

### Variables and channels

We model the warehouse as a 2D matrix `int map[][]`, whose size is calculated
based on the system parameters `N_POD_ROWS` and `N_PODS_PER_ROW_{W,E}`: each
cell holds information about its kind (pod/human/entry/intersection), whether a
robot is present or not, and the default directions for bots to follow. The task
queue is a simple array `int tasks[]` used as a ring buffer. Finally, we keep
track of the availability of each pod through another global array
`bool pod_free[]`.

For synchronization purposes we define the following channels, which are *all*
`urgent broadcast`:

- `init_done`: only used for initialization to signal all templates to start
- `asap`: used to fire a particular transition as soon as possible
- `step`: channel used to synchronize the movement of the bots when one or more
  bots are stuck one behind each other in a queue
- `delivery_ready`: used by the `Bot` template to notify the human that it's
  ready for delivery
- `human_done`: used by the `Human` template to release the currently delivering

Templates
---------

### Initializer

![Initializer Timed Automaton](assets/ta_initializer.png){width=25%}

This is a dummy timed automaton which only has one transition which executes
immediately as the initial state is committed. The `initialize_all()` function
generates the map and initializes global variables. All the other timed
automaton of the system are signaled to start through the `init_done` channel.

### TaskGenerator

This template models the incoming requests for the packages to the warehouse. It
takes a mean and variance as parameter to describe the normal distribution for
the task generation time: $\mathcal{N}(\mu_T, \sigma_T)$.

![TaskGenerator Timed Automaton](assets/ta_taskgenerator.png){width=80%}

It is composed of a single cycle of 4 edges, 3 of which model the normal
distribution. The constants `t_min` and `t_max` are defined as:

\newcommand{\ffrac}[2]{\ensuremath{\frac{\displaystyle #1}{\displaystyle #2}}}

\begin{center}
\texttt{t\_min} $= \ffrac{\mu_T - \sigma_T}{3}$ \hspace{10pt}
\texttt{t\_max} $= \ffrac{\mu_T + \sigma_T}{3}$
\end{center}

The last edge that closes the cycle performs
the actual generation of a task by selecting a free pod that has no robot below
it and enqueueing the task into the global `queue` through the `enqueue()`
helper function. Task generation is done as soon as possible after the initial
delay exploiting the `asap` urgent broadcast channel.

### Human

This template models the behaviour of the human operator. It takes a mean and
variance as parameter to describe the normal distribution for the operator
processing time: $\mathcal{N}(\mu_H, \sigma_H)$.

![Human Timed Automaton](assets/ta_human.png){width=80%}

It is composed of a single cycle of states. The first transition waits for a
robot to show itself through the `delivery_ready` channel. Again, the following
3 edges model the normal distribution in the same way as for `TaskGenerator`.
The last edge that closes the cycle releases the delivering robot through the
`human_done` channel.

### Bot

This template models a single robot and is instantiated `N_BOTS` times. The only
template parameter is the robot's ID.

![Bot Timed Automaton](assets/ta_bot.png){width=80%}

At a high level, after entering the warehouse, each robot continuously cycles
among four *objectives*\footnote{We merely chose the word \textit{objective}
here because in UPPAAL \texttt{state} is a reserved word}: ***pickup***,
***delivery***, ***return***, ***idle***. When not ***idle***, the behavior of a
robot is based on its current *objective* and *objective position* (coordinates
in the map). The initial objective of a robot right after entering the warehouse
is ***pickup***. The behavior of a robot depending on the objective is as
follows:

- ***Pickup*** or ***return***: the *objective position* corresponds to the
  assigned pod. To reach it, the robot follows the default directions for all
  cells *except* intersections (see layout in figure \ref{fig:wh-layout}), in
  which case it checks based on its position whether it needs to enter the aisle
  below the wanted pod's row *or* go up because it just reached the cell right
  under the pod *or* follow the default direction. After ***pickup*** the robot
  changes objective to ***delivery***, while after ***return*** the robot
  becomes ***idle***.

- ***Delivery***: the *objective position* corresponds to the human. The robot
  merely follows the default direction for each cell of the warehouse (see
  layout in figure \ref{fig:wh-layout}). These directions ensure that robots
  always reach the highway regardless of their starting position, and then cycle
  on the highway until the human is reached. After reaching the human, the robot
  signals that the pod has been delivered through the `delivery_ready` channel
  and waits on the `human_done` channel. After this, the objective changes to
  ***return***.

- ***Idle***: the robot stays under the returned pod for a minimum amount of
  time determined by an exponential probability distribution (with $\lambda =$
  `BOT_IDLE_EXP_TIME`), then retrieves a new task from the queue as soon as
  it is available.

The actual movement logic, in terms of step-by-step movements through the cells
of the grid of the warehouse, is implemented in the `maybe_step()` function,
which tries to take a single step based on the robot's current position,
*objective* and *objective position*. If the movement is successful, the robot
advances one cell, otherwise this means that another robot is currently
occupying the target cell: in this case the robot implicitly waits for any other
robot movement through the `step` channel until the target cell becomes free.

## Conflicts between robots

It may happen that more than one robot needs to move to the same cell at the
same time. Whenever a robot needs to move, it first checks if the target cell is
free, and if so it moves to it and marks it as occupied. This conflict is
implicitly solved by the atomicity of transitions provided by UPPAAL. Since
timed automata transitions are executed atomically (even if happening at the
same instant of time), there will always be only one robot moving to the target
cell, and the conflict is avoided altogether.

It may also happen that one or more robots get stuck behind each other in line.
In such case, the `step` urgent broadcast channel makes all robots in the line
move forward as soon as possible, without wasting another `BOT_STEP_TIME` period
per robot.

Finally, all ***idle*** robots try (at the same time) to pick the next available
task from the queue if it is not empty, which raises another possible conflict.
The atomicity of this operation is again guaranteed by the atomicity of
transitions provided by UPPAAL, so there cannot be multiple bots picking the
same task off the queue.
