#!/usr/bin/env python3

print(r'''\documentclass{standalone}
\usepackage{tikz}
\usetikzlibrary{positioning}

\begin{document}
\begin{tikzpicture}[
    node distance = 0.3cm,
    box/.style = {draw, minimum height=0.75cm, fill opacity=0.3, text opacity=1}]

    \pgfdeclarelayer{bg}
    \pgfsetlayers{bg,main}

    \node (wh) [inner sep=0] {
        \tikz {
            \draw[step=1cm,black,thin] (0,0) grid (12,7);''')

grid = '''\
>>>>he<<<<<<
^ppp^vppppp^
^lllXxrrrrr^
^ppp^vppppp^
^lllXxrrrrr^
^ppp^vppppp^
^lllXLrrrrr^'''

grid = grid.splitlines()[::-1]

for y, row in enumerate(grid, 1):
    for x, cell in enumerate(row):
        if cell in ('>', 'h', 'r'):
            ax, ay = x + 0.25, y - 0.25
            bx, by = x + 0.75, y - 0.50
            cx, cy = x + 0.25, y - 0.75
        elif cell in ('<', 'l', 'L'):
            ax, ay = x + 0.75, y - 0.25
            bx, by = x + 0.25, y - 0.50
            cx, cy = x + 0.75, y - 0.75
        elif cell in ('^', 'p', 'X'):
            ax, ay = x + 0.25, y - 0.75
            bx, by = x + 0.50, y - 0.25
            cx, cy = x + 0.75, y - 0.75
        elif cell in ('v', 'x', 'e'):
            ax, ay = x + 0.25, y - 0.25
            bx, by = x + 0.50, y - 0.75
            cx, cy = x + 0.75, y - 0.25
        else:
            continue

        print(f'\\draw[white,fill=black,opacity=0.3] ({ax:.2f},{ay:.2f}) -- ({bx:.2f},{by:.2f}) -- ({cx:.2f},{cy:.2f}) -- cycle;')

        if cell == 'p':
            print(f'\\fill[cyan,opacity=0.3] ({x},{y - 1}) rectangle ({x + 1},{y});')
        elif cell in ('l', 'r'):
            print(f'\\fill[yellow,opacity=0.3] ({x},{y - 1}) rectangle ({x + 1},{y});')
        elif cell in ('x', 'X', 'L'):
            print(f'\\fill[orange,opacity=0.3] ({x},{y - 1}) rectangle ({x + 1},{y});')
        elif cell == 'e':
            print(f'\\fill[green,opacity=0.3] ({x},{y - 1}) rectangle ({x + 1},{y});')
        elif cell == 'h':
            print(f'\\fill[red,opacity=0.3] ({x},{y - 1}) rectangle ({x + 1},{y});')

print(r'''\
            \draw[black,thick] (0,0) -- (0, 7) -- (12, 7) -- (12, 0) -- cycle;
            \draw[blue,ultra thick] (4,7) -- (6, 7) -- (6, 0) -- (4, 0) -- cycle;
        }
    };

    \node (n1) [box, right=of wh.north east, anchor=north west, fill=red] {\textbf{human}};
    \node (n2) [box, below=of n1.south west, anchor=north west, fill=green] {\textbf{entry}};
    \node (n3) [box, below=of n2.south west, anchor=north west, fill=cyan] {\textbf{pod}};
    \node (n4) [box, below=of n3.south west, anchor=north west] {\textbf{intersection}};
    \node (n5) [box, below=of n4.south west, anchor=north west, blue, ultra thick, text=black] {\textbf{highway}};

    \begin{pgfonlayer}{bg}
        \filldraw[yellow,opacity=0.3][] (n4.south west) -- (n4.north west) -- (n4.north east) -- cycle;
        \filldraw[orange,opacity=0.3][] (n4.north east) -- (n4.south east) -- (n4.south west) -- cycle;
    \end{pgfonlayer}
\end{tikzpicture}
\end{document}''')
