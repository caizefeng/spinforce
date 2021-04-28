#!/usr/bin/env python3
# @File    : ndarray_helper.py
# @Time    : 3/19/2021 10:08 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import numpy as np


def cartesian_product(arrays) -> np.ndarray:
    return np.stack(np.meshgrid(*arrays, indexing='ij'), -1).reshape(-1, len(arrays))
