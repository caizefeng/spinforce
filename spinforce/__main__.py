#!/usr/bin/env python3
# @File    : __main__.py
# @Time    : 3/20/2021 3:14 PM
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com

import argparse
import os

from spinforce.SfStructureSpinTask import SfStructureSpinTask
from spinforce import __version__

def main():
    parser = argparse.ArgumentParser(description="Calculate spin forces based on DFT code SPHInX")
    parser.add_argument("-c", nargs='?', help="Configuration JSON location")
    parser.add_argument("config",  nargs='?', help="Configuration JSON location")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)
    example_config_path = os.path.join(os.path.dirname(__file__), "configs/spinforce.json")
    parser.add_argument("--example_config", action='store_true', help="view example configuration JSON at {}".format(
        os.path.abspath(example_config_path)))
    args = parser.parse_args()

    if args.example_config:
        EDITOR = os.environ.get('EDITOR', 'vim')  # use `vim` as default
        os.system("{} {}".format(EDITOR, example_config_path))
    else:
        task = SfStructureSpinTask()
        if args.c:
            task.run(args.c)
        elif args.config:
            task.run(args.config)
        else:
            print('No configuration file provided, use `--example_config` to see a example JSON for configuration!')


if __name__ == '__main__':
    main()
