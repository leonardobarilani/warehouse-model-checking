\newpage

Design
======

Warehouse layout
----------------

We design the warehouse as a rectangular grid of arbitrary size, divided in a
west and east side, each of which holds an equal number of rows of pods, spaced
one cell from each other. Each of the two sides has a (possibly different) fixed
number of pods per row. Between the two sides, there is a central highway
spanning the entire warehouse in height and two columns in width. At most one of
the two sides of pod rows can be completely missing (i.e. having *zero* pods per
row): in such case the highway is positioned completely west or completely east
of the warehouse.

\begin{figure}
\centering
\includegraphics[width=0.85\textwidth,height=\textheight]{build/warehouse_layout.pdf}
\caption{Warehouse layout}
\label{fig:wh-layout}
\end{figure}

The *human operator* can be positioned on an arbitrary cell of the highway,
while the *entry point* can be positioned on an arbitrary cell of the warehouse
that is not already occupied by a pod or by the human operator.

The robots in the warehouse move from cell to cell according to the default
directions defined for each cell, except for *intersection* cells where they can
turn and move in a different direction in order to reach a pod. The robot
behavior and movement is described more in detail in section \ref{bot}.

The above image highlights one of the possible layouts of the warehouse as well
as the default directions that bots will travel. In this case, we have 3 pod
rows, 3 pods-per-row on the west side and 5 pods-per-row on the east side. These
parameters (further described in section \ref{global-declarations}) allow
defining a rectangular warehouse of arbitrary size with arbitrary west-to-east
highway placement.


Stochastic features
-------------------

We model the following stochastic features, where the normal distributions were
implemented directly as transitions on the timed automata following the UPPAAL
SMC
Tutorial\footnote{https://www.it.uu.se/research/group/darts/papers/texts/uppaal-smc-tutorial.pdf}.

- Time elapsed between two tasks with a normal distribution:
  $\mathcal{N}(\mu_T,\,\sigma_T)$
- Delay for a robot to claim a new task with an exponential distribution:
  $\mathcal{X}(\lambda)$
- Human operator processing time with a normal distribution:
  $\mathcal{N}(\mu_H,\,\sigma_H)$


Design assumptions
------------------

The following assumptions were made at the design stage and need to be satisfied
in order for the model to be simulated correctly and meaningfully:

1. The sum of the total number of robots plus the capacity of the task queue is
   strictly less than the number of pods in the warehouse. It does not make
   sense to model a system in which the number of pods is lower than or equal to
   the number of available bots plus the queue capacity: such a system would
   never be able to fail under any time parameter assignment.
2. Pods with idle bots underneath cannot be assigned to any robot as a new task.
   This implies that no robot can be assigned a task corresponding to the same
   pod twice in a row.
3. Entry point and human operator are placed on valid cells, that is: human on
   one of the cells of the highway and entry on any other cell that is not a
   pod.
