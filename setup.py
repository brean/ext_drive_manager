#!/usr/bin/env python3
from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="ext_drive_manager",
    description="Python program to clone drives.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brean/ext_drive_manager",
    version="0.1",
    license="BSD-3",
    author="Andreas Bresser",
    packages=find_packages(),
    tests_require=[],
    package_data={},
    install_requires=[
        'argcomplete',
        'textual',
        'textual-cogs'
    ],
    entry_points={
        'console_scripts': [
            'ext_drive_manager = ext_drive_manager.cli:main',
        ],
    }
)