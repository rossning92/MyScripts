import os
import tempfile

from _shutil import shell_open
from utils.math import animate_function


def quadratic(x, a):
    return a * x * x


if __name__ == "__main__":
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)

    file = animate_function(
        quadratic,
        var="a",
        varmin=1,
        varmax=2,
        xmin=-2,
        xmax=2,
        ymin=0,
        ymax=4,
        title="y = a*x^2",
        xlabel="x",
        ylabel="y",
    )

    shell_open(file)
