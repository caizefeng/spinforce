#!/usr/bin/env python3
# @File    : sigma.py
# @Time    : 3/11/2021 5:37 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com

import numpy as np

energy = np.loadtxt("energy.dat")
print(np.abs(energy[:, 2] - energy[:, 3])[-1] * 27.21 / 2)
