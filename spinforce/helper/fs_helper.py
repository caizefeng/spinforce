#!/usr/bin/env python3
# @File    : fs_helper.py
# @Time    : 3/19/2021 10:18 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import os


def mkdir_without_override(path):
    if not os.path.exists(path):
        os.makedirs(path)


def batch_remove_if_exists(*paths):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)
