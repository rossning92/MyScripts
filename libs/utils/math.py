import functools
import os
from typing import Optional

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


def animate_function(
    func,
    var,
    varmin=-1.0,
    varmax=1.0,
    xmin=0.0,
    xmax=1.0,
    ymin=0.0,
    ymax=1.0,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
) -> str:

    _ = plt.figure()
    (line,) = plt.plot([], [])
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.gca().set_aspect("equal", adjustable="box")
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)

    def animate(t):
        xs = np.linspace(xmin, xmax, 100)
        f = functools.partial(func, **{var: t})
        vec_func = np.vectorize(f)
        ys = vec_func(xs)

        line.set_data(xs, ys)

        plt.title("%s%s = %.2f" % (title + "\n" if title else "", var, t))
        plt.gcf().tight_layout()

        return (line,)

    anim = animation.FuncAnimation(
        plt.gcf(),
        animate,
        frames=(np.sin(np.arange(0.0, 2.0 * np.pi, 0.05)) + 1.0)
        * 0.5
        * (varmax - varmin)
        + varmin,
        interval=10,
        blit=True,
        repeat=False,
    )

    file = f"animated-function-{func.__name__}-{var}=({varmin},{varmax}).gif"
    anim.save(
        file,
        writer="imagemagick",
        fps=25,
    )
    return os.path.abspath(file)
