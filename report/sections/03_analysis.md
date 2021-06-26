Analysis and results
====================

Model analysis
--------------

In order to find meaningful configurations, we analyzed the probability of
losing any task (i.e. exceeding the task queue capacity) through the following
query:

\begin{center}\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}\end{center}

We ran two different multi-parameter tests of the same query varying 3 different
parameters at a time using the `verifyta`[^verifyta] command line tool and
plotting the results. In both tests the entry point and the human operator are
always respectively at the north-east and south-east cell of the highway. All
SMC parameters were left at their default values except for *probability
uncertainty* which we set to $\epsilon = 0.01$ to get more accurate results.

\bgroup
\def\arraystretch{0.75}
| **Parameter**       | **Test A**                                | **Test B**                       |
|:--------------------|:------------------------------------------|:---------------------------------|
| `N_BOTS`            | 5                                         | $\in [3, 10] \subset \mathbb{N}$ |
| `N_POD_ROWS`        | 5                                         | 5                                |
| `N_PODS_PER_ROW_W`  | $\in [0, 10] \subset \mathbb{N}$          | 5                                |
| `N_PODS_PER_ROW_E`  | 10 $-$ \texttt{N\_PODS\_PER\_ROW\_W}      | 5                                |
| `QUEUE_CAPACITY`    | $\in [1, 5, 10, 15, 20]$                  | $\in [1, 10] \subset \mathbb{N}$ |
| `TASK_GEN_MEAN`     | $\in [10, 20] \subset \mathbb{N}$         | $\in [5, 20] \subset \mathbb{N}$ |
| `TASK_GEN_VAR`      | 5                                         | 1                                |
| `HUMAN_MEAN`        | 2                                         | 2                                |
| `HUMAN_VAR`         | 1                                         | 1                                |
| `BOT_IDLE_EXP_RATE` | 3                                         | 3                                |
| `BOT_STEP_TIME`     | 1                                         | 1                                |
| `TAU`               | 10000                                     | 10000                            |
\egroup

\todo{maybe fix queue capacity and vary N\_BOTS on test A?}

The main purpose of **Test A** is to asses the effect of different highway
placements: on the vertical axis we vary the position of the highway from East
to West of the warehouse. The main purpose of **Test B** is to asses the impact
of the queue capacity under different task generation frequencies and with
different numbers of robots.

![4D plots of test results - one dot per data point](assets/4d_plots.png)

From the results of **Test A**, we conclude that (unsurprisingly) a centered
highway placement is better than a lateral one. From **Test B**, we conclude
that **the capacity of the task queue only marginally affects the efficiency of
the warehouse**: a small queue capacity ($< 5$) is enough in any configuration
where the robots are capable of completing tasks in a timely manner, otherwise
*even with higher queue capacities* the queue will eventually fill up and tasks
will start getting lost (in these situations, there always exists a `TAU` large
enough for the warehouse to start losing tasks).

[^verifyta]: https://docs.uppaal.org/toolsandapi/verifyta


First property: efficient warehouse
-----------------------------------

From the analysis performed in the previous section, we extract a relevant data
point where the warehouse rarely loses tasks. The system parameters are
configured as follows:

\bgroup
\def\arraystretch{0.75}
+---------------------+-------------------------------------------+
| `N_BOTS`            | 10                                        |
+---------------------+-------------------------------------------+
| `N_POD_ROWS`        | 5                                         |
+---------------------+-------------------------------------------+
| `N_PODS_PER_ROW_W`  | 5                                         |
+---------------------+-------------------------------------------+
| `N_PODS_PER_ROW_E`  | 5                                         |
+---------------------+-------------------------------------------+
| `QUEUE_CAPACITY`    | 5                                         |
+---------------------+-------------------------------------------+
| `TASK_GEN_MEAN`     | 8                                         |
+---------------------+-------------------------------------------+
| `TASK_GEN_VAR`      | 5                                         |
+---------------------+-------------------------------------------+
| `HUMAN_MEAN`        | 2                                         |
+---------------------+-------------------------------------------+
| `HUMAN_VAR`         | 1                                         |
+---------------------+-------------------------------------------+
| `BOT_IDLE_EXP_RATE` | 3                                         |
+---------------------+-------------------------------------------+
| `BOT_STEP_TIME`     | 1                                         |
+---------------------+-------------------------------------------+
| `ENTRY_POS`         | { r = 0, c = 7 } (north-east of highway)  |
+---------------------+-------------------------------------------+
| `ENTRY_POS`         | { r = 10, c = 7 } (south-east of highway) |
+---------------------+-------------------------------------------+
| `TAU`               | 10000                                     |
+---------------------+-------------------------------------------+
\egroup

The probability of losing a task is calculated through the query:

\begin{center}\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}\end{center}

Which yields: $P_{tasks\_lost > 0} \le xxx$.
\todo{add result}


Second property: inefficient warehouse
--------------------------------------
