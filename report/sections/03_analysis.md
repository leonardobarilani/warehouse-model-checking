Analysis and results
====================

We first performed a multi-parameter analysis to find meaningful system
configurations, then extracted two non-trivial configurations to test analyze
the system under the two requested scenarios: one with high efficiency and one
with low efficiency.

Multi-parameter analysis
------------------------

We analyzed the warehouse efficiency in terms of the probability of losing any
task (i.e. exceeding the task queue capacity) through the following query:

\vspace{-10pt}
\begin{center}\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}\end{center}
\vspace{-10pt}

We built an ad-hoc Python test suite\footnote{Source code available at
https://github.com/leonardobarilani/warehouse-model-checking (see README.md)} to
vary 3 independent parameters in different ranges, verifying each different
configuration using the
`verifyta`\footnote{https://docs.uppaal.org/toolsandapi/verifyta} command line
tool bundled with UPPAAL
4.1.25\footnote{https://uppaal.org/downloads/other/\#uppaal-41}, plotting the
results using Matplotlib\footnote{https://matplotlib.org}. In the end, we
extracted two meaningful tests, both of which were configured with the following
parameters and run with default SMC parameters except for *probability
uncertainty* set to $\varepsilon = 0.01$.

\bgroup
\def\arraystretch{0.8}
\begin{center}
\rowcolors{2}{gray!10}{white}
\begin{tabular}{ | l | l | l | }
	\hline
	\textbf{System parameter} & \textbf{Test A value} & \textbf{Test B value}\\
	\hline
	\texttt{N\_BOTS}                          & 5                                    & $\in [3, 10] \subset \mathbb{N}$ \\
	\texttt{N\_POD\_ROWS}                     & 5                                    & 5                                \\
	\texttt{N\_PODS\_PER\_ROW\_W}             & $\in [0, 10] \subset \mathbb{N}$     & 5                                \\
	\texttt{N\_PODS\_PER\_ROW\_E}             & 10 $-$ \texttt{N\_PODS\_PER\_ROW\_W} & 5                                \\
	\texttt{QUEUE\_CAPACITY}                  & $\in [1, 5, 10, 15, 20]$             & $\in [1, 10] \subset \mathbb{N}$ \\
	\texttt{TASK\_GEN\_MEAN} ($\mu_T$)        & $\in [10, 20] \subset \mathbb{N}$    & $\in [5, 20] \subset \mathbb{N}$ \\
	\texttt{TASK\_GEN\_VAR} ($\sigma_T$)      & 5                                    & 1                                \\
	\texttt{HUMAN\_MEAN} ($\mu_H$)            & 2                                    & 2                                \\
	\texttt{HUMAN\_VAR} ($\sigma_H$)          & 1                                    & 1                                \\
	\texttt{BOT\_IDLE\_EXP\_RATE} ($\lambda$) & 3                                    & 3                                \\
	\texttt{BOT\_STEP\_TIME}                  & 1                                    & 1                                \\
	\texttt{ENTRY\_POS}                       & top of highway east column           & top of highway east column       \\
	\texttt{ENTRY\_POS}                       & bottom of highway east column        & bottom of highway east column    \\
	\texttt{TAU}                              & 10000                                & 10000                            \\
	\hline
\end{tabular}
\end{center}
\egroup

The main purpose of **Test A** is to asses the effect of different highway
placements: we keep the number of pods and pod rows fixed and vary the position
of the highway from East to West of the warehouse.

The main purpose of **Test B** is to asses the impact of the queue capacity
under different task generation frequencies and with different workloads (task
generation mean time) and different numbers of robots.

![4D plots of probability of losing tasks - one data point per configuration](assets/4d_plots.png)

From the results of **Test A**, we conclude that (unsurprisingly) a centered
highway placement is better than a lateral one. From the results of **Test B**,
we observe that *the capacity of the task queue only marginally affects the
efficiency of the warehouse*. The probability of not losing tasks does not scale
linearly along with the queue capacity. Fixed other system parameters, there
seems to be a clear breakpoint for the queue capacity before which losing tasks
is very likely and after which is very unlikely. Choosing a capacity that is
above this breakpoint is thus unneeded.

From the above graph for **Test B**, we can in fact see that for a warehouse of
50 pods with a centered highway, if the bots are capable of completing tasks in
a timely manner, a queue capacity of 4 is enough to not lose tasks even in the
most stressful system configurations, otherwise *higher queue capacities* do not
solve the problem; the queue will eventually fill up and tasks will start
getting lost.


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
