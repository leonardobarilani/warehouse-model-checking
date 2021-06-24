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

The *human operator* can be positioned on an arbitrary cell of the highway,
while the *entry point* can be positioned on an arbitrary cell of the warehouse
that is not already occupied by a pod or by the human operator.

\begin{figure}
\centering
\includegraphics[width=0.85\textwidth,height=\textheight]{build/warehouse_layout.pdf}
\caption{Warehouse layout}
\label{fig:wh-layout}
\end{figure}

The above image highlights one of the possible layouts of the warehouse as well
as the default directions that bots will travel. In this case, we have 3 pod
rows, 3 pods-per-row on the west side and 5 pods-per-row on the east side. These
parameters (further described in section \ref{global-declarations}) allow
defining a rectangular warehouse of arbitrary size with arbitrary west-to-east
highway placement.

Stochastic features
-------------------

We model the following stochastic features:

- Time elapsed between two tasks with a normal distribution:
  $\mathcal{N}(\mu_T,\,\sigma_T)$
- Delay for a robot to claim a new task with an exponential distribution:
  $\mathcal{X}(\lambda)$
- Human operator processing time with a normal distribution:
  $\mathcal{N}(\mu_H,\,\sigma_H)$

The normal distributions were implemented directly as transitions on the timed
automata following the
[UPPAAL SMC Tutorial](http://people.cs.aau.dk/~adavid/publications/89-tutorial.pdf).

Design assumptions
------------------

The following assumptions were made at the design stage and need to be satisfied
in order for the model to be simulated correctly and meaningfully:

1. The sum of the total number of robots plus the capacity of the task queue is
   strictly less than the number of pods in the warehouse. It does not make
   sense to model a system in which the number of pods is lower than or equal to
   the number of available bots plus the queue capacity: such a system would
   never be able to fail under any time parameter assignment.
2. Pods with idle bots underneath cannot be assigned to any bot as a new task.
   This implies that no bot can be assigned a task corresponding to the same pod
   twice in a row.
