#!/usr/bin/env python
from setuptools import setup

setup(
    name="nettigo",
    version="0.0.4",
    author="Maciej Bieniek",
    author_email="maciej.bieniek@gmail.com",
    description="Python wrapper for getting air quality data from Nettigo Air Monitor devices.",
    include_package_data=True,
    url="https://github.com/bieniu/nettigo",
    license="Apache-2.0 License",
    packages=["nettigo"],
    python_requires=">=3.6",
    install_requires=list(val.strip() for val in open("requirements.txt")),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    setup_requires=("pytest-runner"),
)
