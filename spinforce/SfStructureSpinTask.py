#!/usr/bin/env python3
# @File    : config_io.py
# @Time    : 3/19/2021 9:33 AM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com
import json
import logging
import os
import subprocess

from spinforce.DPIO import DPWriter
from spinforce.SfLogging import SfLogging
from spinforce.SfSpinTask import SfSpinTask


class SfStructureSpinTask:
    def __init__(self):
        self._working_dir = None; self._structure_dir = None; self._structure_paths = []
        self._spin_dir = None
        self._spin_paths = []
        self._config_dir = None
        self._input_path = None

        self._output_dir = None

        self._sphinx_path = None

        self._tags = []
        self._default_constraint = None
        self._single_task = SfSpinTask()
        self._dp_writer = DPWriter()
        self._logging_generator = SfLogging()
        self._logger = None  # type: logging.Logger

    @property
    def working_dir(self):
        return self._working_dir

    @working_dir.setter
    def working_dir(self, value):
        self._working_dir = value
        self._logger.info("Working directory: {}".format(value))

    @property
    def structure_dir(self):
        return self._structure_dir

    @structure_dir.setter
    def structure_dir(self, value):
        value = self.check_join_wd(value)
        self.structure_paths, tag_list = self.load_dir(value, "structure.sx")
        self.load_check_tag(tag_list)
        self._structure_dir = value
        self._logger.info("Structure files at {}".format(value))

    @property
    def structure_paths(self):
        return self._structure_paths

    @structure_paths.setter
    def structure_paths(self, value):
        self._structure_paths = value
        self._logger.info("All structure files: {}".format(value))

    @property
    def spin_dir(self):
        return self._structure_dir

    @spin_dir.setter
    def spin_dir(self, value):
        value = self.check_join_wd(value)
        self.spin_paths, tag_list = self.load_dir(value, "spin.sx")
        self.load_check_tag(tag_list)
        self._spin_dir = value
        self._logger.info("Spin files at {}".format(value))

    @property
    def spin_paths(self):
        return self._spin_paths

    @spin_paths.setter
    def spin_paths(self, value):
        self._spin_paths = value
        self._logger.info("All spin files: {}".format(value))

    @property
    def config_dir(self):
        return self._config_dir

    @config_dir.setter
    def config_dir(self, value):
        value = self.check_join_wd(value)
        self._config_dir = value
        self._logger.info("Configuration files at {}".format(value))

    @property
    def input_path(self):
        return self._input_path

    @input_path.setter
    def input_path(self, value):
        value = self.check_join_wd(value)
        self._input_path = value
        self._logger.info("Input file template: {}".format(value))

    @property
    def output_dir(self):
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value):
        value = self.check_join_wd(value)
        self._output_dir = value
        self._logger.info("Output DP raw files at {}".format(value))

    @property
    def sphinx_path(self):
        return self._sphinx_path

    @sphinx_path.setter
    def sphinx_path(self, value):
        check_version = "{} --version | grep \"S/PHI/nX\"".format(value)
        sub = subprocess.Popen(check_version, shell=True, stdout=subprocess.PIPE)
        if not sub.stdout.read():
            self._logger.error("Invalid SPHInX binary specified!")
            raise RuntimeError
        self._sphinx_path = value
        self._logger.info("SPHInX binary used: {}".format(value))

    def load_check_tag(self, tag_list):
        if self._tags:
            if tag_list != self._tags:
                self._logger.error("Structure and spin files are not of one-to-one correspondence. Task stop!")
                raise RuntimeError
        else:
            self._tags = tag_list

    def load_dir(self, value, basename):
        file_paths = [x.path for x in os.scandir(value) if x.name.endswith(basename)]
        if not file_paths:
            self._logger.error("There is no {} files in the specified directory!".format(basename))
            raise RuntimeError
        file_paths.sort(key=lambda x: int(os.path.basename(x).split("_")[0]))
        tag_list = [int(os.path.basename(x).split("_")[0]) for x in file_paths]
        return file_paths, tag_list

    def check_join_wd(self, value):
        if not os.path.isabs(value):
            return os.path.join(self._working_dir, value)
        else:
            return value

    def read_config(self, task_config_file):
        self._logger.info("Loading configuration from file {}".format(os.path.abspath(task_config_file)))
        with open(task_config_file, "r") as f:
            config = json.load(f)

            file_system_dict = config["sphinx_file"]
            # use setter method to log
            self.working_dir = file_system_dict["working_dir"]
            self.structure_dir = file_system_dict["structure_dir"]
            self.spin_dir = file_system_dict["spin_dir"]
            self.config_dir = file_system_dict["config_dir"]
            self.input_path = file_system_dict["input_path"]
            self.output_dir = config["dp_file"]["output_dir"]

            self._dp_writer.init(self._output_dir)

            self.sphinx_path = config["sphinx_path"]

            if "spin_constraint" in config.keys():
                self._default_constraint = config["spin_constraint"]

    def run(self, task_config_file):
        self._logger = self._logging_generator.get_logger("TaskTag")
        self._dp_writer._logger = self._logging_generator.get_logger("DPWriter")
        self._single_task._logger = self._logging_generator.get_logger("TaskVariant")

        self.read_config(task_config_file)
        self._logger.info("Loading finished\n")

        os.chdir(self._working_dir)
        os.system("rm -f *.dat *.sxb relaxedStr.sx relaxHist.sx forces.sx output.sx")

        self._logger.info("Task begins\n")
        self._single_task._config_dir = self._config_dir
        self._single_task._input_file = self._input_path
        self._single_task._sphinx_path = self._sphinx_path
        self._single_task._default_constraint = self._default_constraint
        self._single_task._dp_writer = self._dp_writer

        for tag, structure_file, spin_file in zip(self._tags, self._structure_paths, self._spin_paths):
            self._single_task.tag = tag
            self._single_task.structure_file = structure_file
            self._single_task.spin_file = spin_file
            self._single_task.run()

        self._dp_writer.close()
        self._logger.info("Task done")
