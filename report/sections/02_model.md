UPPAAL Model
============

Global Declarations
-------------------

### System parameters

+---------------------+----------------------------------------------------------+
| `N_BOTS`            | Number of robots in the warehouse                        |
+---------------------+----------------------------------------------------------+
| `N_POD_ROWS`        | Number of rows of pods in the warehouse                  |
+---------------------+----------------------------------------------------------+
| `N_PODS_PER_ROW_W`  | Number of pods per single row on the warehouse West side |
+---------------------+----------------------------------------------------------+
| `N_PODS_PER_ROW_E`  | Number of pods per single row on the warehouse East side |
+---------------------+----------------------------------------------------------+
| `QUEUE_CAPACITY`    | Capacity of the tasks' queue                             |
+---------------------+----------------------------------------------------------+
| `TASK_GEN_MEAN`     | Task generation mean time ($\mu_T$)                      |
+---------------------+----------------------------------------------------------+
| `TASK_GEN_VAR`      | Task generation time variance ($\sigma_T$)               |
+---------------------+----------------------------------------------------------+
| `HUMAN_MEAN`        | Human operator mean reaction time ($\mu_H$)              |
+---------------------+----------------------------------------------------------+
| `HUMAN_VAR`         | Human operator reaction time variance ($\sigma_H$)       |
+---------------------+----------------------------------------------------------+
| `BOT_IDLE_EXP_RATE` | Robot task claim delay ($\lambda$ of exponential         |
|                     | distribution)                                            |
+---------------------+----------------------------------------------------------+
| `BOT_STEP_TIME`     | Time needed for a robot to move between adjacent tiles   |
+---------------------+----------------------------------------------------------+
| `TAU`               | Upper time bound for verification                        |
+---------------------+----------------------------------------------------------+

### Variables and channels

We model the warehouse as a 2D matrix `int map[][]`, whose size is calculated
based on the system parameters `N_POD_ROWS` and `N_PODS_PER_ROW_{W,E}`: each
cell holds information about its kind (pod/human/entry/intersection), wheter a
bot is present or not, and the default directions for bots to follow. The task
queue is a simple array `int tasks[]` used as a ring buffer. The availability of
each pod is kept track of through another global array `bool pod_free[]`.

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

This is a dummy timed automata which only has one transition which executes
immediately as the initial state is committed. On the transition, an
initialization function is executed to initialize the whole system performing
map generation and global variable initialization according to system
parameters.

### TaskGenerator

This template models the incoming requests for the packages to the warehouse. It
takes a mean and variance as parameter to describe the normal distribution for
the task generation time: $\mathcal{N}(\mu_T, \sigma_T)$.

![TaskGenerator Timed Automata](assets/ta_taskgenerator.png){width=80%}

It is composed of a single cycle of 4 edges, 3 of which model the normal
distribution. The last edge that closes the cycle performs the actual generation
of a task by selecting a free pod that has no robot below it and enqueueing the
task into the global `queue` through the `enqueue()` helper function. Task
generation is done as soon as possible after the initial delay exploiting the
`asap` urgent broadcast channel.

### Human

This template models the behaviour of the human operator. It takes a mean and
variance as parameter to describe the normal distribution for the operator
processing time: $\mathcal{N}(\mu_H, \sigma_H)$.

![Human Timed Automata](assets/ta_human.png){width=80%}

It is composed of a single cycle of states. The first transition waits for a
robot to show itself through the `delivery_ready` channel. Again, the following
3 edges model the normal distribution. The last edge that closes the cycle
releseas the delivering robot through the `human_done` channel.

### Bot

This template models a single robot and is instantiated `N_BOTS` times. The only
template parameter is the bot's ID.

![Bot Timed Automata](assets/ta_bot.png){width=80%}

At a high level, after entering the warehouse, each robot continuously cycles
among four macro-states: ***pickup***, ***delivery***, ***return***, ***idle***.
When not ***idle***, the behavior of a robot is based on its current *objective*
and *objective position* (coordinates in the map).

- ***Delivery***: the *objective position* corresponds to the human. Robots
   merely follow the default direction for each cell of the warehouse (see
   layout in figure \ref{fig:wh-layout}). These directions ensure that robots
   always reach the highway regardless of their starting position, and then
   cycle on the highway until the human is reached. After reaching the human,
   the robot notifies it through the `delivery_ready` channel and waits on the
   `human_done` channel. After this, the objective changes to ***return***.

- ***Pickup*** or ***return***: the *objective position* corresponds to the
   assigned pod. To reach it, the robot follows the default directions for all
   cells *except* intersections (see layout in figure \ref{fig:wh-layout}), in
   which case it checks based on its position whether it needs to [1] enter the
   aisle below the wanted pod's row or [2] go up because it just reached the
   cell right under the pod or [3] follow the default direction. After
   ***pickup*** the bot changes objective to ***delivery***, while after
   ***return*** the bot becomes ***idle***.

- ***Idle***: the robot stays under the returned pod for a minimum amount of
  time determined by an exponential probability distribution (with $\lambda =$
  `BOT_IDLE_EXP_TIME`), then retrieves a new task from the queue as soon as
  it is available.

The actual movement logic, in terms of step-by-step movements through the cells
of the grid of the warehouse, is implemented in the `maybe_step()` function,
which tries to take a single step based on the robot's current position,
*objective* and *objective position*. If the movement is successful, the bot
advances one cell, otherwise it implicitly waits through the `step` channel for
the bot that is currently occupying the cell to move.

### Conflicts between robots

It may happen that more than one robot needs to move to the same cell. Whenever
a robot needs to move, it first checks if the target cell is free, and if so it
moves to it and marks it as occupied. This conflict is implicitly solved by the
atomicity of transitions provided by UPPAAL. Since timed automata transitions
are executed atomically (even if happening at the same instant of time), there
will always be only one bot moving to the target cell, and the conflict is
avoided altogether.

It may also happen that one or more robots get stuck one behind the other in
line. In such case, the `step` urgent broadcast channel makes all robots in the
line move forward as soon as possible, without wasting another `BOT_STEP_TIME`
period per robot.

Finally, all ***idle*** robots try (at the same time) to pick the next available
task from the queue if it is not empty, which raises another possible conflict.
The atomicity of this operation is again guaranteed by the atomicity of
transitions provided by UPPAAL, so there cannot be multiple bots picking the
same task off the queue.
