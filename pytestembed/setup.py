#!/usr/bin/env python3
"""Setup script for PyTestEmbed library."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "PyTestEmbed - Embed tests and documentation within Python class and method definitions"

setup(
    name="pytestembed",
    version="0.1.0",
    author="PyTestEmbed Team",
    author_email="team@pytestembed.dev",
    description="Embed tests and documentation within Python class and method definitions",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/pytestembed/pytestembed",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Documentation",
    ],
    python_requires=">=3.8",
    install_requires=[
        "textX>=3.0.0",
        "click>=8.0.0",
        "transformers>=4.20.0",
        "torch>=1.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "pytestembed=pytestembed.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pytestembed": ["*.tx", "*.json"],
    },
)
