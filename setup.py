#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    requirements = []
    for line in f:
        requirements.append(line)

setup(
    name="phantombatch",
    version="0.0.1",
    author="Josh Calcino",
    author_email="josh.calcino@gmail.com",
    description=("A tool to run multiple phantom simulations."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshcalcino/phantombatch",
    packages=["phantombatch"],
    license="MIT",
    install_requires=None,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
