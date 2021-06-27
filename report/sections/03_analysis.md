Analysis and results
====================

We first performed a multi-parameter analysis to find meaningful system
configurations, then extracted two non-trivial configurations to analyze the
system under the two requested scenarios: one with high efficiency and one with
low efficiency.

Multi-parameter analysis
------------------------

We analyzed the warehouse efficiency in terms of the probability of losing any
task (i.e. exceeding the task queue capacity) through the following query:

\vspace{-10pt}
\begin{center}\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}\end{center}
\vspace{-10pt}

We built an ad-hoc Python test suite\footnote{See README.md at
https://github.com/leonardobarilani/warehouse-model-checking} to vary 3
independent parameters in different ranges, verifying each different
configuration using the
`verifyta`\footnote{https://docs.uppaal.org/toolsandapi/verifyta} command line
tool bundled with UPPAAL
4.1.25\footnote{https://uppaal.org/downloads/other/\#uppaal-41}, plotting the
results using Matplotlib\footnote{https://matplotlib.org}. We created two
multi-parameter tests, configured according to the following table, and ran them
with default SMC parameters except for *probability uncertainty* set to
$\varepsilon = 0.01$.

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
	\texttt{QUEUE\_CAPACITY}                  & $\in \{1, 5, 10, 15, 20\}$           & $\in [1, 10] \subset \mathbb{N}$ \\
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

The main purpose of **Test A** is to assess the effect of different highway
placements: we keep the number of pods and pod rows fixed and vary the position
of the highway from East to West of the warehouse.

The main purpose of **Test B** is to assess the impact of the queue capacity
under different task generation frequencies and with different workloads (task
generation mean time) and different numbers of robots.

![4D plots of probability of losing any task - one data point per configuration](assets/4d_plots.png)

From the results of **Test A**, we conclude that (unsurprisingly) a centered
highway placement is better than a lateral one. From the results of **Test B**,
we observe that *the capacity of the task queue only marginally affects the
efficiency of the warehouse*. The probability of not losing tasks does not scale
linearly along with the queue capacity. Fixed other system parameters, there
seems to be a clear breakpoint for the queue capacity before which losing any
task is very likely and after which is very unlikely. Choosing a capacity that
is above this breakpoint is thus unneeded.

From the above graph for **Test B**, we can in fact see that for a warehouse of
50 pods with a centered highway, if the bots are capable of completing tasks in
a timely manner, a queue capacity of 4 is enough to not lose tasks even in the
most stressful system configurations, otherwise *higher queue capacities* do not
solve the problem; the queue will eventually fill up and tasks will start
getting lost. However, it is worth noting that what we are testing here is
continuous operation of the warehouse. In a real-life scenario where the
warehouse may *not* be continuously operational 24 hours a day, a large enough
queue (based on the maximum time of continuous operation per day) could actually
solve the problem.

\newpage

First scenario: efficient warehouse
-----------------------------------

From the analysis performed in the previous section, we extract a relevant
system configuration where the warehouse rarely loses tasks. Here we have a
warehouse with 50 total pods distributed evenly between West and East and 10
robots.

System and SMC parameters are configured as follows (non-default SMC values in
bold):

\bgroup
\def\arraystretch{0.8}
\rowcolors{2}{gray!10}{white}
\begin{center}
\begin{tabular}{ | l | l | }
	\hline
	\textbf{System parameter} & \textbf{Value} \\
	\hline
	\texttt{N\_BOTS}                          & 10 \\
	\texttt{N\_POD\_ROWS}                     & 5 \\
	\texttt{N\_PODS\_PER\_ROW\_W}             & 5 \\
	\texttt{N\_PODS\_PER\_ROW\_E}             & 5 \\
	\texttt{QUEUE\_CAPACITY}                  & 5 \\
	\texttt{TASK\_GEN\_MEAN} ($\mu_T$)        & 8 \\
	\texttt{TASK\_GEN\_VAR} ($\sigma_T$)      & 5 \\
	\texttt{HUMAN\_MEAN} ($\mu_H$)            & 2 \\
	\texttt{HUMAN\_VAR} ($\sigma_H$)          & 1 \\
	\texttt{BOT\_IDLE\_EXP\_RATE} ($\lambda$) & 3 \\
	\texttt{BOT\_STEP\_TIME}                  & 1 \\
	\texttt{ENTRY\_POS}                       & $\{ 0, 7 \}$ (highway north-east)  \\
	\texttt{HUMAN\_POS}                       & $\{ 10, 7 \}$ (highway south-east) \\
	\texttt{TAU}                              & 10000 \\
	\hline
\end{tabular}
\quad
\rowcolors{2}{gray!10}{white}
\begin{tabular}{ | c | l | }
	\hline
	\textbf{SMC parameter} & \textbf{Value} \\
	\hline
	$\pm\delta$         & 0.01 \\
	$\alpha$            & \textbf{0.01} \\
	$\beta$             & \textbf{0.01} \\
	$\varepsilon$       & \textbf{0.01} \\
	$u_0$               & 0.9  \\
	$u_1$               & 1.1  \\
	Trace resolution    & 4096 \\
	Discretization step & 0.01 \\
	\hline
\end{tabular}
\end{center}
\egroup

We calculated the efficiency of the warehouse (as probability of losing any
task) again through the following query to get an exact result:

\vspace{-10pt}
\begin{center}
\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}
\end{center}
\vspace{-5pt}

Which yields Pr $\in [0, 0.0199955]$ with a confidence of 99% (over 228 runs).

We finally calculated the expected maximum number of tasks waiting in the queue
at any given time through the following query, where `tasks_in_queue` is a
global counter updated when enqueueing/dequeueing:

\vspace{-10pt}
\begin{center}
\texttt{E [<= TAU; 1000] (max: tasks\_in\_queue)}
\end{center}
\vspace{-10pt}

Which yields the following probability distribution:

![Scenario 1: probability distribution of maximum tasks in queue](assets/s1_queue_prob.png){width=70%}

The average maximum number of tasks in the queue over 1000 runs is $2.502 \pm
0.045$. The queue rarely gets filled up to 4 tasks, and it does not seem to be
ever holding 5 tasks.


Second scenario: inefficient warehouse
--------------------------------------

Always from the analysis performed in the previous section, we extract a second
relevant data point where the warehouse almost certainly loses tasks.

Here's the full list of system and SMC parameters. There are only 3 system
parameters which are different from the previous scenario, with the new values
highlighted in bold:

\bgroup
\def\arraystretch{0.8}
\rowcolors{2}{gray!10}{white}
\begin{center}
\begin{tabular}{ | l | l | }
	\hline
	\textbf{System parameter} & \textbf{Value} \\
	\hline
	\texttt{N\_BOTS}                          & 10 $\rightarrow$ \textbf{7} \\
	\texttt{N\_POD\_ROWS}                     & 5 \\
	\texttt{N\_PODS\_PER\_ROW\_W}             & 5 \\
	\texttt{N\_PODS\_PER\_ROW\_E}             & 5 \\
	\texttt{QUEUE\_CAPACITY}                  & 5 $\rightarrow$ \textbf{10} \\
	\texttt{TASK\_GEN\_MEAN} ($\mu_T$)        & 8 $\rightarrow$ \textbf{10} \\
	\texttt{TASK\_GEN\_VAR} ($\sigma_T$)      & 5 \\
	\texttt{HUMAN\_MEAN} ($\mu_H$)            & 2 \\
	\texttt{HUMAN\_VAR} ($\sigma_H$)          & 1 \\
	\texttt{BOT\_IDLE\_EXP\_RATE} ($\lambda$) & 3 \\
	\texttt{BOT\_STEP\_TIME}                  & 1 \\
	\texttt{ENTRY\_POS}                       & $\{ 0, 7 \}$ (highway north-east)  \\
	\texttt{HUMAN\_POS}                       & $\{ 10, 7 \}$ (highway south-east) \\
	\texttt{TAU}                              & 10000 \\
	\hline
\end{tabular}
\quad
\rowcolors{2}{gray!10}{white}
\begin{tabular}{ | c | l | }
	\hline
	\textbf{SMC parameter} & \textbf{Value} \\
	\hline
	$\pm\delta$         & 0.01 \\
	$\alpha$            & 0.01 \\
	$\beta$             & 0.01 \\
	$\varepsilon$       & 0.01 \\
	$u_0$               & 0.9  \\
	$u_1$               & 1.1  \\
	Trace resolution    & 4096 \\
	Discretization step & 0.01 \\
	\hline
\end{tabular}
\end{center}
\egroup

As for the previous scenario, we calculated the warehouse efficiency again with
the same query:

\vspace{-10pt}
\begin{center}
\texttt{Pr [<= TAU] (<> tasks\_lost > 0)}
\end{center}
\vspace{-10pt}

Which now yields Pr $\in [0.980005, 1]$ with a confidence of 99% (over 228 runs).

In this case UPPAAL also produces probability distribution graphs, so we
exported the cumulative probability distribution of exceeding the queue capacity
and starting to lose tasks over time:

![Scenario 2: cumulative probability distribution of losing any task over time](assets/s2_task_lost_prob.png){width=70%}

Given enough time, roughly half of our simulation upper bound (`TAU`), the
system becomes almost certainly (Pr $\approx 1$) unable to handle the workload
and starts losing tasks.

\newpage

Finally, taking a look at the probability distribution of the total number of
completed tasks versus the total number of lost tasks using the following two
queries:

\vspace{-10pt}
\begin{center}
\texttt{E [<= TAU; 1000] (max: tasks\_completed)} \\
\texttt{E [<= TAU; 1000] (max: tasks\_lost)}
\end{center}
\vspace{-10pt}

We obtain the following results:

![Scenario 2: probability distribution of maximum number of completed tasks](assets/s2_max_tasks_completed_prob.png){width=100%}

![Scenario 2: probability distribution of maximum number of lost tasks](assets/s2_max_tasks_lost_prob.png){width=100%}

With an average of $1065.490 \pm 0.381$ tasks completed and $30.587 \pm 0.672$
tasks lost over 1000 runs.
