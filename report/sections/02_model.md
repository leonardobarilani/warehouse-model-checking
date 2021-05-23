\newpage

UPPAAL Model
============

Global Declarations
-------------------

### Parameters

+---------------------+--------------------------------------------------------+
| **Parameter**       | **Description**                                        |
+---------------------+--------------------------------------------------------+
| `N_BOTS`            | Number of robots in the warehouse                      |
+---------------------+--------------------------------------------------------+
| `N_POD_ROWS`        | Number of rows of pods in the warehouse                |
+---------------------+--------------------------------------------------------+
| `N_PODS_PER_ROW`    | Number of pods per single row                          |
+---------------------+--------------------------------------------------------+
| `QUEUE_CAPACITY`    | Capacity of the tasks' queue                           |
+---------------------+--------------------------------------------------------+
| `TASK_GEN_MEAN`     | Task generation mean time ($\mu_T$)                    |
+---------------------+--------------------------------------------------------+
| `TASK_GEN_VAR`      | Task generation time variance ($\sigma_T$)             |
+---------------------+--------------------------------------------------------+
| `HUMAN_MEAN`        | Human operator mean reaction time ($\mu_H$)            |
+---------------------+--------------------------------------------------------+
| `HUMAN_VAR`         | Human operator reaction time variance ($\sigma_H$)     |
+---------------------+--------------------------------------------------------+
| `BOT_IDLE_EXP_RATE` | Robot task claim delay ($\lambda$ of exponential       |
|                     | distribution)                                          |
+---------------------+--------------------------------------------------------+
| `BOT_STEP_TIME`     | Time needed for a robot to move between adjacent tiles |
+---------------------+--------------------------------------------------------+
| `TAU`               | Upper time bound for verification                      |
+---------------------+--------------------------------------------------------+

### Variables and channels

We model the warehouse as a 2D matrix `int map[][]`, whose size is calculated
based on the number of pod rows and pods per row. The task queue is a simple
array `int tasks[]` used as a ring buffer.

For synchronization purposes we define the following channels, which are *all*
`urgent broadcast`:

- `asap`: used to fire a particular transition as soon as possible
- `init_done`: only used for initialization to signal all templates to start
- `human_done`: used by the `Human` template to release the currently delivering
  robot
- `delivery_ready`: used by the `Bot` template to notify the human that it's
  ready for delivery

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

It is composed by a single cycle of states. The first edge waits for a robot to
show itself through the `delivery_ready` channel. Again, the following 3 edges
model the normal distribution. The last edge that closes the cycle releseas the
delivering robot through the `human_done` channel.

### `Bot`

![`Bot` Timed Automata](assets/ta_bot.png)
