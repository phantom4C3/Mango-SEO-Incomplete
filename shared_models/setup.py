# shared_models/setup.py
from setuptools import setup

setup(
    name="shared_models",
    version="0.1.0",
    packages=['shared_models'],  # Explicitly specify the package name
    package_dir={'shared_models': '.'},  # Tell setuptools where to find the package
    install_requires=[
        "pydantic>=2.0",
    ],
)