#!/usr/bin/env python3
# @File    : compare_spin_force.py
# @Time    : 3/19/2021 8:11 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import os

import numpy as np

from spinforce.SphinxIO import SphinxIO


def compare_spin_force(atom_idx, interval):
    spins = np.loadtxt('spin-constraint.sx')
    spins_plus = spins.copy()
    spins_plus[atom_idx] += interval / 2
    spins_minus = spins.copy()
    spins_minus[atom_idx] -= interval / 2

    run_sphinx()
    final_spin_list, nu_list = SphinxIO.read_final_spin_and_nu()
    # print(final_spin_list)
    # print(spins)
    if not SphinxIO.check_constraint(spins, final_spin_list):
        raise RuntimeError("Incomplete constraint")

    write_spin(spins_plus)
    run_sphinx()
    energy_plus = SphinxIO.read_final_energy()
    final_spin_list_plus, nu_list_plus = SphinxIO.read_final_spin_and_nu()
    if not SphinxIO.check_constraint(spins_plus, final_spin_list_plus):
        raise RuntimeError("Incomplete constraint")

    write_spin(spins_minus)
    run_sphinx()
    energy_minus = SphinxIO.read_final_energy()
    final_spin_list_minus, nu_list_minus = SphinxIO.read_final_spin_and_nu()
    if not SphinxIO.check_constraint(spins_minus, final_spin_list_minus):
        raise RuntimeError("Incomplete constraint")

    spin_force = (energy_plus - energy_minus) / interval
    print(f"Hellmann-Feynman Spin force: {nu_list[atom_idx]}")
    print(f"Finite difference Spin force: {spin_force}")


def write_spin(spins):
    np.savetxt("spin-constraint.sx", spins)
    os.system("cp spin-constraint.sx spin-initial.sx")


def run_sphinx():
    sphinx_path = "/home/lzhpc/anaconda3/envs/sphinx/bin/sphinx"
    os.system("{} > output.sx".format(sphinx_path))

# os.chdir("")
compare_spin_force(0, 0.01)

