#!/usr/bin/env python3
# @File    : SfConfigParser.py
# @Time    : 3/20/2021 9:32 AM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com

import logging
import sys


class SfLogging:

    def __init__(self):
        self._root_name = "SpinForce"
        self._root_logger = logging.getLogger(self._root_name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        self._ch = logging.StreamHandler(sys.stdout)
        self._ch.setFormatter(formatter)
        self._root_logger.addHandler(self._ch)
        self._root_logger.setLevel(logging.INFO)

    def get_logger(self, subname) -> logging.Logger:
        return logging.getLogger('.'.join((self._root_name, subname)))  # child logger
