# -*- coding: utf-8 -*-
import numpy as np


N = 600

t = np.arange(0, N, 1).reshape(-1, 1)
t = np.array([t[i] + np.random.rand(1) / 4 for i in range(len(t))])
t = np.array([t[i] - np.random.rand(1) / 7 for i in range(len(t))])
t = np.array(np.round(t, 2))

x1 = np.round((np.random.random(N) * 5).reshape(-1, 1), 2)
x2 = np.round((np.random.random(N) * 5).reshape(-1, 1), 2)
x3 = np.round((np.random.random(N) * 5).reshape(-1, 1), 2)

n = np.round((np.random.random(N) * 2).reshape(-1, 1), 2)

y = np.array(
    [((np.log(np.abs(2 + x1[t])) - x2[t - 1] ** 2) + 0.02 * x3[t - 3] * np.exp(x1[t - 1])) for t in range(len(t))]
)
y = np.round(y + n, 2)
