#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OrbiTraj
========

An USCF Chimera extension that patches MD Movie extension
to import volume data for each frame. Useful for orbital
trajectories (hence the name), and maybe other uses.
"""

from Movie import restoreSession
from Trajectory import EnsembleLoader
from .core import OrbiTrajController


def launch(movieFile=None):
    EnsembleLoader.loadEnsemble(OrbiTrajController, movieFile=movieFile)
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
