#!/usr/bin/env python3
# @File    : sphinx_io.py
# @Time    : 3/18/2021 1:24 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import re
import subprocess as sp
from typing import Tuple

import numpy as np


class SphinxIO:
    @staticmethod
    def read_final_energy():
        get_energy_cmd = 'tail -1 energy.dat | awk \'{print $5}\''
        sub = sp.Popen(get_energy_cmd, shell=True, stdout=sp.PIPE)
        total_energy = float(str(sub.stdout.read(), 'utf-8'))
        sub.kill()
        return total_energy

    @staticmethod
    def read_final_spin_and_nu():
        get_spin_cmd = 'grep -A 3 \"nu(0)\" output.sx | tail -4'
        sub = sp.Popen(get_spin_cmd, shell=True, stdout=sp.PIPE)
        spin_info = str(sub.stdout.read(), 'utf-8')
        sub.kill()
        final_spin_array = np.array(
            [float(i) for i in re.findall(r'^Spin of atom \d = (.*?)$', spin_info, flags=re.MULTILINE)])
        nu_array = np.array([float(i) for i in re.findall(r'^nu\(\d*\) = (.*?)$', spin_info, flags=re.MULTILINE)])
        return final_spin_array, nu_array

    @staticmethod
    def check_constraint(spin_array, final_spin_array):
        return not any(np.abs(spin_array - final_spin_array) > 1e-5)

    @staticmethod
    def check_convergence() -> Tuple[bool, bool, int]:
        convergence_reached = False
        steps_over = True
        get_convergence_cmd = 'grep \"Convergence reached.\" output.sx'
        sub = sp.Popen(get_convergence_cmd, shell=True, stdout=sp.PIPE)
        matched_line = str(sub.stdout.read(), 'utf-8')
        if matched_line:  # not empty
            convergence_reached = True
        sub.kill()

        if convergence_reached:
            get_step_cmd = 'grep -B 1 \"Convergence reached.\" output.sx | head -n 1'
            sub = sp.Popen(get_step_cmd, shell=True, stdout=sp.PIPE)
            line = str(sub.stdout.read(), 'utf-8')
            num_step = int(re.findall(r'F\((\d+)\)=', line)[0])
            steps_over = False
            sub.kill()
        else:
            get_step_cmd = 'grep -B 2 \"Convergence not yet reached.\" output.sx | head -n 1'
            sub = sp.Popen(get_step_cmd, shell=True, stdout=sp.PIPE)
            line = str(sub.stdout.read(), 'utf-8')
            if line:  # terminated by step limitation
                num_step = int(re.findall(r'F\((\d+)\)=', line)[0])
                sub.kill()
            else:  # terminated from other error
                sub.kill()
                get_step_cmd = 'grep \"F(\" output.sx | tail -n 1'
                sub = sp.Popen(get_step_cmd, shell=True, stdout=sp.PIPE)
                new_line = str(sub.stdout.read(), 'utf-8')
                num_step = int(re.findall(r'F\((\d+)\)=', new_line)[0])
                steps_over = False
                sub.kill()

        return convergence_reached, steps_over, num_step

    @staticmethod
    def read_structure():
        with open("structure.sx", "r") as f:
            content = f.read()

            # cell parameter
            cell_parameter = re.findall(r'\s*cell\s*?=\s*?(.*?)\s*;', content, flags=re.DOTALL)[0]  # type: str
            cell_parameter = re.sub(r'[\[\]\n]', '', cell_parameter)
            cell = np.fromstring(cell_parameter, dtype=float, sep=',').reshape((3, 3))

            coord_pattern = r'atom\s*{\s*coords\s*=(.*?)\s*;'
            structure_dict, structure_array = SphinxIO.read_atomwise_info(content, coord_pattern, cell)

        return cell, structure_dict, structure_array

    @staticmethod
    def expand_collinear(entry):
        entry_array = np.zeros(len(entry) * 3)
        for i, entry_z in enumerate(entry):
            entry_array[(i + 1) * 3 - 1] = entry_z
        return entry_array

    @staticmethod
    def read_spin(structure_dict, is_collinear=True):
        spin_raw = np.loadtxt("spin-constraint.sx")
        spin_dict = {}
        spin_list = []
        idx = 0
        for atom_type, coords in structure_dict.items():
            spin_dict[atom_type] = []
            for _ in range(len(coords)):
                if is_collinear:
                    spin = np.array([0., 0., spin_raw[idx]])
                    spin_dict[atom_type].append(spin)
                    spin_list.append(spin)
                    idx += 1
                else:
                    NotImplemented

        for atom_type, spins in spin_dict.items():
            spin_dict[atom_type] = np.array(spins)

        spin_array = np.array(spin_list).reshape(-1)
        return spin_dict, spin_array

    @staticmethod
    def read_force():

        with open("forces.sx", "r") as f:
            content = f.read()
            force_pattern = r'force\s*=(.*?)\s*;'
            force_dict, force_array = SphinxIO.read_atomwise_info(content, force_pattern)

        return force_dict, force_array

    @staticmethod
    def read_atomwise_info(content, entry_pattern, cell: np.ndarray = None):
        lines = content.split('\n')
        entry_dict = {}
        entry_list = []
        current_type = -1

        for line in lines:
            pure_line = line.strip()
            if pure_line[0:2] != "//":  # not a comment
                element = re.findall(r'element\s*=\s*"(.*)"\s*;', pure_line)
                entry_raw = re.findall(entry_pattern, pure_line)
                if element:
                    current_type += 1
                    entry_dict[str(current_type)] = []
                elif entry_raw:
                    entry = np.fromstring(entry_raw[0].strip(' []'), dtype=float, sep=',')

                    # only for atom coordinates occasion
                    is_relative = ("relative" in pure_line)
                    if is_relative:
                        entry = entry @ cell

                    entry_dict[str(current_type)].append(entry)
                    entry_list.append(entry)

        for atom_type, entry in entry_dict.items():
            entry_dict[atom_type] = np.array(entry)  # list to ndarray

        entry_array = np.array(entry_list).reshape(-1)
        return entry_dict, entry_array
