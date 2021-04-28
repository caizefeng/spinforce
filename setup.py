#!/usr/bin/env python3
# @File    : setup.py.py
# @Author  : Zavier Cai
# @Email   : caizefeng18@gmail.com

import codecs
import os.path

import setuptools


# def get_readme():
#     with open('README.md', 'r', encoding='utf-8') as f:
#         return f.read()


def get_required_packages():
    with open('requirements.txt', 'r') as f:
        return f.read().splitlines()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            print(line)
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name='spinforce',
    version=get_version("spinforce/__init__.py"),
    description='Calculate spin forces based on DFT code SPHInX',
    # long_description=get_readme(),
    # long_description_content_type='text/markdown',
    author='Zavier Cai',
    author_email='caizefeng18@gmail.com',
    url='',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    keywords='spin-force SPHInX constraint',
    # project_urls={
    #     'Documentation': 'https://packaging.python.org/tutorials/distributing-packages/',
    # },
    packages=setuptools.find_packages(),
    install_requires=get_required_packages(),
    python_requires='>=3.6',
    package_data={
        'spinforce': ['templates/*', 'configs/*'],

    },
    # data_files=[('my_data', ['data/data_file'])],
    entry_points={
        'console_scripts': [
            'spinforce=spinforce.__main__:main',
        ],
    },
)
