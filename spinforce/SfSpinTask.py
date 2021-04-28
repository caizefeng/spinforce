#!/usr/bin/env python3
# @File    : SfSpinTask.py
# @Time    : 3/19/2021 3:46 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com

import json
import logging
import os
from typing import Dict

import numpy as np

from spinforce.DPIO import DPWriter
from spinforce.SphinxIO import SphinxIO
from spinforce.helper.ndarray_helper import cartesian_product


class SfSpinTask:
    def __init__(self):

        self._tag = None
        self._structure_file = None
        self._spin_file = None

        self._config_dir = None
        self._config_file = None
        self._input_file = None

        self._sphinx_path = None

        self._constraint = None
        self._default_constraint = None

        self._changing_atom_indices = []
        self._changing_spins = []
        self._num_samples = 0

        self._dp_writer = None  # type: DPWriter
        self._logger = None  # type: logging.Logger

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value
        self._logger.info("Task for Tag {} begins".format(value))

    @property
    def structure_file(self):
        return self._structure_file

    @structure_file.setter
    def structure_file(self, value):
        self._structure_file = value
        self._logger.info("Atomic structure read from {}".format(value))

    @property
    def spin_file(self):
        return self._spin_file

    @spin_file.setter
    def spin_file(self, value):
        self._spin_file = value
        self._logger.info("Spin read from {}".format(value))

    def search_constraint_config(self):
        if not os.path.exists(self._config_dir):
            self._config_file = None
        else:
            for x in os.scandir(self._config_dir):
                if x.name.endswith("spinforce.json"):
                    if self._tag == x.name.split("_")[0]:
                        self._config_file = x.path

    def read_constraint_config(self):
        if self._config_file:
            with open(self._config_file, "r") as f:
                self._constraint = json.load(f)
            self._logger.info("Using constraints in file {} for Tag {}".format(self._config_file, self._tag))
        else:
            self._logger.info(
                "Corresponding constraints not found, using default constraints for Tag {}".format(self._tag))
            self._constraint = self._default_constraint

    def parse_constraint(self):
        indices = []
        samples_list = []
        if self._constraint["collinear"]:
            self._logger.info("Using collinear spin calculation and constraints for Tag {}".format(self._tag))
            for constraint in self._constraint["atoms"]:
                indices.append(constraint["index"])
                samples_list.append(self.sampling_spin(constraint["sampling"], constraint["bound"]))
        else:
            self._logger.info("Using non-collinear spin calculation and constraints for Tag {}".format(self._tag))
            NotImplemented

        self._changing_atom_indices = indices
        self._changing_spins = cartesian_product(samples_list).T.tolist()
        self._num_samples = len(self._changing_spins[0])
        self._logger.info("Indices of spin-varied atoms in this tag: {}\n".format(indices))

    def sampling_spin(self, sampling, bound_dict: Dict):

        low = bound_dict["low"]
        high = bound_dict["high"]

        if sampling == "uniform":

            if "interval" in bound_dict.keys():
                if "points" in bound_dict.keys():
                    self._logger.warning(
                        "Entry \"interval\" and \"points\" are both in the configuration, using \"interval\" anyway!")
                spin_samples = np.arange(low, high + bound_dict["interval"], bound_dict["interval"])
            elif "points" in bound_dict.keys():
                spin_samples = np.linspace(low, bound_dict["high"], bound_dict["points"], endpoint=True)
            else:
                self._logger.error("One of \"interval\"/\"points\" must be specified!")
                raise RuntimeError

        elif sampling == "random":
            if not ("points" in bound_dict.keys()):
                self._logger.error("\"random\" sampling must be used with \"points\" specified!")
                raise RuntimeError
            spin_samples = np.random.uniform(low, high, bound_dict["points"])

        else:
            self._logger.error("Invalid sampling method \"{}\"!".format(sampling))
            raise RuntimeError
        return spin_samples

    def run(self):
        self.search_constraint_config()
        self.read_constraint_config()
        self.parse_constraint()

        # pre-processing
        os.system("cp {} input.sx".format(self._input_file))
        os.system("cp {} structure.sx".format(self._structure_file))
        spin_temp = np.loadtxt(self._spin_file)  # 1D array without x/y components if collinear
        for calc_count in range(self._num_samples):
            self._logger.info("Calculation begins for Tag {} Variant {}".format(self._tag, calc_count))
            for atom_idx in self._changing_atom_indices:
                spin_temp[atom_idx] = self._changing_spins[atom_idx][calc_count]
            np.savetxt("spin-constraint.sx", spin_temp)
            os.system("cp spin-constraint.sx spin-initial.sx")

            cell, structure_dict, structure_array = SphinxIO.read_structure()
            spin_dict, spin_array = SphinxIO.read_spin(structure_dict, self._constraint["collinear"])

            # running SPHInX
            self._logger.info("All files prepared, running SPHInX ...")
            os.system("{} > output.sx".format(self._sphinx_path))

            # post-processing
            final_spin, nu = SphinxIO.read_final_spin_and_nu()
            if self._constraint["collinear"]:
                nu_array = SphinxIO.expand_collinear(nu)
                final_spin_array = SphinxIO.expand_collinear(final_spin)
            else:
                nu_array = nu
                final_spin_array = final_spin

            convergence_reached, steps_over, num_step = SphinxIO.check_convergence()
            constraint_reached = SphinxIO.check_constraint(spin_array, final_spin_array)  # both are 3N long
            if (not convergence_reached) and steps_over:
                self._logger.warning(
                    "Convergence not yet reached within {} steps in Tag {} Variant {}, this frame won't be written to DP raw files!".format(
                        num_step, self._tag, calc_count))
                self._logger.warning("Current spin constraints is {}\n".format(spin_array))
            if (not constraint_reached) and (not steps_over):
                self._logger.warning(
                    "Incomplete spin constraints within {} steps in Tag {} Variant {}, this frame won't be written to DP raw files!".format(
                        num_step, self._tag, calc_count))
                self._logger.warning("Current spin constraints is {}\n".format(spin_array))
            else:
                force_dict, force_array = SphinxIO.read_force()
                total_energy = SphinxIO.read_final_energy()

                self._dp_writer.write_box(cell)
                self._dp_writer.write_coord(structure_array, spin_array)
                self._dp_writer.write_type(structure_dict)  # should change to one time
                self._dp_writer.write_energy(total_energy)
                self._dp_writer.write_force(force_array, nu_array)

                self._logger.info(
                    "Calculation successfully finished within {} steps for Tag {} Variant {}".format(num_step,
                                                                                                     self._tag,
                                                                                                     calc_count))
                self._logger.info("Current spin constraints is {}\n".format(spin_array))
