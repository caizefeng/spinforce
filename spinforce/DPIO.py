#!/usr/bin/env python3
# @File    : dp_io.py
# @Time    : 3/18/2021 3:38 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import logging
import os

import numpy as np

from spinforce.helper.fs_helper import mkdir_without_override, batch_remove_if_exists


class DPWriter:
    def __init__(self):
        self.f_box = None
        self.f_coord = None
        self.f_type = None
        self.f_energy = None
        self.f_force = None
        self._logger = None  # type: logging.Logger
        self._type_written = None
        self._num_frames = None
        self._affine_parameter = None

    def init(self, output_dir):
        self._num_frames = 0
        self._affine_parameter = 0.5

        mkdir_without_override(output_dir)
        box_path = os.path.join(output_dir, "box.raw")
        coord_path = os.path.join(output_dir, "coord.raw")
        type_path = os.path.join(output_dir, "type.raw")
        energy_path = os.path.join(output_dir, "energy.raw")
        force_path = os.path.join(output_dir, "force.raw")

        batch_remove_if_exists(box_path, coord_path, type_path, energy_path, force_path)

        self.f_box = open(box_path, "a+")
        self.f_coord = open(coord_path, "a+")
        self.f_type = open(type_path, "a+")
        self.f_energy = open(energy_path, "a+")
        self.f_force = open(force_path, "a+")

        self._logger.info(
            "Using affine parameter {} to generate pseudo-coordinates from spins".format(self._affine_parameter))

    def close(self):
        self.f_box.flush()
        self.f_coord.flush()
        self.f_type.flush()
        self.f_energy.flush()
        self.f_force.flush()

        self.f_box.close()
        self.f_coord.close()
        self.f_type.close()
        self.f_energy.close()
        self.f_force.close()

        self._logger.info("{} frames overall have been successfully written".format(self._num_frames))

    def write_box(self, cell):
        # Bohr, reshape to write on one line
        np.savetxt(self.f_box, cell.reshape((1, -1)))
        self.f_box.flush()
        self._num_frames += 1

    def write_coord(self, coord_array, spin_array):
        np.savetxt(self.f_coord,
                   np.concatenate(
                       (coord_array, self.spin2pseudo_coords(coord_array, spin_array, self._affine_parameter))).reshape(
                       (1, -1)))
        self.f_coord.flush()

    def write_type(self, structure_dict):

        type_list = []
        for atom_type, coords in structure_dict.items():
            type_list.extend(np.repeat(int(atom_type), len(coords)).tolist())
        type_array = np.array(type_list, dtype=int)
        type_array = np.concatenate((type_list, type_array + len(structure_dict)))

        if self._type_written is None:  # only write once
            np.savetxt(self.f_type, type_array.reshape((1, -1)), fmt='%4d')
            self.f_type.flush()
            self._type_written = type_array
        elif any(self._type_written != type_array):
            self._logger.error("Atom type not consistent between frames!")
            raise RuntimeError

    def write_force(self, force_array, nu_array):
        # Hartree / Bohr, Hartree / a.u. (~ 2 mu_B)
        np.savetxt(self.f_force, np.concatenate((force_array, nu_array)).reshape((1, -1)))
        self.f_force.flush()

    def write_energy(self, total_energy):
        # Hartree
        self.f_energy.write(str(total_energy) + '\n')
        self.f_energy.flush()

    @staticmethod
    def spin2pseudo_coords(coord_array, spin_array, affine_parameter):
        return coord_array + affine_parameter * spin_array

    def write_spin(self):
        NotImplemented
