"""PyTestEmbed - Embed tests and documentation within Python class and method definitions.

This package provides tools to parse custom syntax that embeds tests and documentation
directly within Python class and method definitions, generate standard Python test code,
and compile unified documentation.
"""

__version__ = "0.1.0"
__author__ = "PyTestEmbed Team"
__email__ = "team@pytestembed.dev"

from .parser import PyTestEmbedParser
from .generator import TestGenerator
from .doc_generator import DocGenerator
from .runner import TestRunner

__all__ = [
    "PyTestEmbedParser",
    "TestGenerator", 
    "DocGenerator",
    "TestRunner",
]
