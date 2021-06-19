\newpage

UPPAAL Model
============

Global Declarations
-------------------

### Parameters

+---------------------+----------------------------------------------------------+
| **Parameter**       | **Description**                                          |
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
based on the number of pod rows and pods per row. The task queue is a simple
array `int tasks[]` used as a ring buffer.

For synchronization purposes we define the following channels, which are *all*
`urgent broadcast`:

- `asap`: used to fire a particular transition as soon as possible
- `step`: channel used to synchronize the movement of the bots when one or more
  bots are stuck one behind each other in a queue
- `init_done`: only used for initialization to signal all templates to start
- `delivery_ready`: used by the `Bot` template to notify the human that it's
  ready for delivery
- `human_done`: used by the `Human` template to release the currently delivering

Templates
---------

### `Initializer`

Only composed of 2 states: the initial one is set as committed so that the
initialization is performed by default as the very first thing once the system
is started. The only transition executes an initialization function to
initialize the whole system. The most important task of this function is to
generate the global `map`.

### `TaskGenerator`

This template models the incoming requests for the packages to the warehouse. It
takes a mean and variance as parameter to describe the normal distribution for
the task generation time: $\mathcal{N}(\mu_T, \sigma_T)$.

![`TaskGenerator` Timed Automata](assets/ta_taskgenerator.png)

It is composed of a single cycle of 4 edges, 3 of which model the normal
distribution. The last edge that closes the cycle performs the actual generation
of a task by selecting a free pod that has no robot below it and enqueueing the
task into the global `queue` through the `enqueue()` helper function. Task
generation is done as soon as possible after the initial delay exploiting the
`asap` urgent broadcast channel.

### `Human`

This template models the behaviour of the human operator. It takes a mean and
variance as parameter to describe the normal distribution for the operator
reaction time: $\mathcal{N}(\mu_H, \sigma_H)$.

![`Human` Timed Automata](assets/ta_human.png)

It is composed of a single cycle of states. The first edge waits for a robot to
show itself through the `delivery_ready` channel. Again, the following 3 edges
model the normal distribution. The last edge that closes the cycle releseas the
delivering robot through the `human_done` channel.

### `Bot`

This template models a single robot and is instantiated `N_BOTS` times. The only
template parameter is the bot's ID.

![`Bot` Timed Automata](assets/ta_bot.png)

After the initial entrance in the warehouse, at any given time a robot can
either be *busy* with an assigned task or *idle* sitting under the last returned
pod waiting for a new task. At a higher level, after entering the warehouse, a
robot can be seen as a timed automata continuously cycling among four
macro-states: *pickup*, *delivery*, *return*, *idle*.

#### Robot movement

When *busy* with a task, the movement of a robot is only based on its current
*objective* and *objective position* (coordinates in the map). The possible
objectives are:

1. **Pickup**: the robot needs to reach the location of the pod corresponding to
   its currently assigned task in order to pick up the pod. After *pickup*, the 
   objective is simply changed to *delivery*.
2. **Delivery**: the robot needs to reach the human to deliver the pod. After
   reaching the human, the robot notifies it through the `delivery_ready`
   channel and waits for it to finish, listening on the `human_done` channel.
   After this, the objective changes to *return*.
3. **Return**: the robot needs to reach the (now empty) pod location in order to
   return the pod. Upon completing objective, the bot marks the current task as
   completed, then enters an *idle* state, where it waits a minimum amount of
   time based on an exponential distribution with a given $\lambda$ global
   parameter.

The actual movement logic, in terms of step-by-step movements through the cells
of the grid of the warehouse, is implemented in the `maybe_step()` function,
which tries to take a single step based on the robot's current position,
objective and objective position. If the movement is successful, the bot steps
forward one cell towards the current objective following the available
directions, otherwise it waits for the bot occupying the cell to move.

There is no real difference between *delivery* and *return* in terms of movement
logic, the only difference is the action that needs to be performed when
reaching the objective.

#### Movement conflicts and congestion resolution

It may happen that more than one robot needs to move to the same cell, causing
a "conflict". This conflict is implicitly solved by the atomicity of transitions
provided by UPPAAL: whenever a robot needs to move, it first checks if the
target cell is free, and if so it moves to it and marks it as occupied. Since
timed automata transitions are executed atomically (even if happening at the
same instant of time), there will always be only one bot moving to the target
cell, and the conflict is avoided altogether.

It may also happen that one or more robots get stuck one behind the other in
line. In such case, the `step` urgent broadcast channel is used to make all
robots in the line move forward as soon as possible, without wasting another
`BOT_STEP_TIME` period per robot.
