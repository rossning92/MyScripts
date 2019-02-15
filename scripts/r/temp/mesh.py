import matplotlib.pyplot as plt
import numpy as np
from numpy.linalg import norm

x = np.linspace(-1, 1, 16)
y = np.linspace(-1, 1, 16)
x, y = np.meshgrid(x, y)

# plt.show()

for i in range(16):
    for j in range(16):
        v = np.array([x[i, j], y[i, j]])
        r = norm(v)
        v *= (8 - r * r)
        x[i, j] = v[0]
        y[i, j] = v[1]

plt.axis('equal')
plt.scatter(x, y)
plt.plot(x, y, 'k')
plt.plot(y, x, 'k')
plt.axis('off')
plt.savefig('1.png')
