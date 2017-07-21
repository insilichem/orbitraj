#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Documentation here.
"""
# Stdlib
from __future__ import print_function, division
from distutils.spawn import find_executable
from types import MethodType
from tkFileDialog import askopenfilenames
import os
from subprocess import Popen, PIPE
# Chimera
import chimera
from chimera.statusline import show_message
import _chimera
import VolumeViewer
from VolumeViewer import open_volume_file
from Trajectory.EnsembleLoader import loadEnsemble
from SurfaceColor import Volume_Color, Gradient_Color, standard_color_palettes, Color_Map
# Own
from gui import OrbiTrajDialog, OrbiTrajConfigDialog

MULTIWFN_SUPPORTED_EXTENSIONS = '.wfn .wfx .fch .molden .gms'.split() + ['.{}'.format(i) for i in xrange(31, 41)]


class OrbiTrajController(object):

    DEFAULT_ISOLEVEL = 0.88
    DEFAULT_COLORMAP = 'rainbow'
    DEFAULT_RGBA = 0.7, 0.7, 0.7, 0.5
    
    def __init__(self, ensemble, *args, **kwargs):
        self.ensemble = ensemble
        self.gui = OrbiTrajDialog(self, ensemble, *args, **kwargs)
        self._volumes = []
        self._patch_MovieDialog()
        self.colormap = None
        self.volume_ui = None

    def refresh(self, volumes=None):
        if volumes is None:
            volumes = self.volumes
        for volume in volumes:
            volume.show()

    @property
    def volumes(self):
        return self._volumes

    @volumes.setter
    def volumes(self, values):
        for value in values:
            if isinstance(value, VolumeViewer.Volume):
                self._volumes.append(value)
            else:
                print("Warning: skipping unsupported value", value)
    
    @volumes.deleter
    def volumes(self):
        chimera.openModels.close(self._volumes)
        self._volumes = []

    def add_volumes(self, paths):
        if not paths:
            return
        if len(paths) != len(self.ensemble):
            raise ValueError('Provide exactly one volume per frame.')
        
        volumes = []
        for i, path in enumerate(paths):
            basename, ext = os.path.splitext(path)
            if ext in MULTIWFN_SUPPORTED_EXTENSIONS:
                show_message('Converting to cube...')
                path = _multiwfn_to_cube(path)
                show_message('Converting to cube... Done!', blankAfter=3)
            volume = open_volume_file(path, show_dialog=False, model_id=1000 + i)[0]
            volume.display = False
            volumes.append(volume)
        
        self.volumes = volumes
        self.isosurface()
        self.colorize_by_volume(alpha=0.6)
        self.update_volume()
        self.volume_ui = self.launch_orbitraj_dialog()

    def update_volume(self, n=None):
        if not self.volumes:
            return
        if n is None:
            n = self.gui.molFrameNum()
        if 0 < n <= len(self.ensemble):
            for volume in self.volumes:
                volume.display = False
            self.volumes[n-1].display = True

    def colorize(self, volumes=None, color=None):
        if color is None:
            color = self.DEFAULT_RGBA
        elif isinstance(color, _chimera.MaterialColor):
            rgba = color.rgba() 
        elif color in chimera.colorTable.colors:
            rgba = chimera.colorTable.getColorByName(color)
        else:
            raise TypeError('Color not recognized.')
        if volumes is None:
            volumes = self.volumes
        for volume in volumes:
            for piece in volume.surfacePieces:
                piece.color = color
    
    def opacity(self, volumes=None, alpha=None):
        if volumes is None:
            volumes = self.volumes
        if alpha is None:
            alpha = self.DEFAULT_RGBA[-1]
        
        if self.colormap is not None:
            self.colormap = [c[:3] + (alpha,) for c in self.colormap]
            for volume in volumes:
                volume.mask.set_colormap(self.colormap)
                volume.mask.color_surface_pieces(volume.surfacePieces)
        else:
            for volume in volumes:
                for piece in volume.surfacePieces:
                    piece.color = piece.color[:3] + (alpha,)
 
    def colorize_by_volume(self, volumes=None, color_source=None, mask='gradient',
                           palette='rainbow', alpha=None):
        if volumes is None:
            volumes = self.volumes
        if color_source is None:
            color_source = volumes
        if mask == 'gradient':
            Mask = Gradient_Color
        elif mask == 'volume':
            Mask = Volume_Color
        else:
            raise ValueError('`mask` must be `gradient` or `volume`')
        palette = standard_color_palettes.get(palette, palette)
        if alpha is not None and 0 <= alpha <= 1:
            palette = tuple(c[:3] + (alpha,) for c in palette)
        all_value_ranges = []
        for volume, color in zip(volumes, color_source):
            mask = Mask()
            mask.set_volume(color)
            value_ranges = []
            for piece in volume.surfacePieces:
                vrange = mask.value_range(piece)
                if None not in vrange:
                    value_ranges.append(vrange)
            value_range = min(zip(*value_ranges)[0]), max(zip(*value_ranges)[1])
            all_value_ranges.append(value_range)
        value_range = min(zip(*all_value_ranges)[0]), max(zip(*all_value_ranges)[1])
        values = list(interpolate_range_into_n_values(value_range, len(palette)))
        self.colormap = Color_Map(values, palette)
        for volume, color in zip(volumes, color_source):
            volume.mask = Mask()
            volume.mask.set_volume(color)
            volume.mask.set_colormap(self.colormap)
            volume.mask.color_surface_pieces(volume.surfacePieces)
            
    def isosurface(self, volumes=None, level_1=0.0, level_2=None):
        """
        Change the cutoffs that define the isosurface extracted from the opened
        volume.

        Parameters
        ----------
        volumes : list of VolumeViewer.volume
            The volumes whose isosurfaces will be edited
        level_1, level_2 : float
            Cutoffs. Defaults are 0.00 and cls.DEFAULT_ISOLEVEL, respectively.
        """
        if level_2 is None:
            level_2 = self.DEFAULT_ISOLEVEL
        if volumes is None:
            volumes = self.volumes
        for volume in volumes:
            volume.surface_levels = level_1, level_2

    def smoothen(self, volumes=None, step=1):
        """
        Smoothening factor of the surface. Best is 1, worst is 8.

        Parameters
        ----------
        volume : list of VolumeViewer.volume
            The volumes whose isosurfaces will be edited
        step : int, optional, default=1
            Smoothening factor. Must be 1, 2, 4, or 8.
        """
        if volumes is None:
            volumes = self.volumes
        if step not in (1, 2, 4, 8):
            return
        ijk_step = [step] * 3
        for volume in volumes:
            if volume.region is None or (ijk_step) == tuple(volume.region[2]) :
                return

            ijk_min, ijk_max = volume.region[:2]
            volume.new_region(ijk_min, ijk_max, ijk_step, adjust_step=False, show=False)

    def launch_orbitraj_dialog(self):
        dialog = OrbiTrajConfigDialog(self, self.gui)
        dialog.enter()
        return dialog

    def _patch_MovieDialog(self):
        """
        Patch original LoadFrame method of Movie.gui.MovieDialog
        to include volume display and .emQuit to remove them.
        """
        self.gui._Original_LoadFrame = self.gui._LoadFrame
        def patched_load_frame(cls, fn, makeCurrent):
            self.gui._Original_LoadFrame(fn, makeCurrent)
            self.update_volume(fn)
        self.gui._LoadFrame = MethodType(patched_load_frame, self.gui)

        self.gui._Original_destroy = self.gui.destroy
        def patched_destroy(cls):
            print('Quitting')
            chimera.openModels.close(self.volumes)
            if self.volume_ui is not None:
                self.volume_ui.destroy()
            self.gui._Original_destroy()
        self.gui.destroy = MethodType(patched_destroy, self.gui)

def interpolate_range_into_n_values(vrange, n):
    """
    Given an interval, subdivide that interval in `n-1` chunks, so we obtain `n` values.
    """
    a, b = vrange
    if a is None:
        a = -1e3
    if b is None:
        b = 1e3
    yield a
    delta = (b - a) / float(n-1)
    for i in range(1, n):
        a = a + delta
        yield a

def _multiwfn_to_cube(path):
    """
    Converts a .wfn file in a Gaussian .cub volume
    using Multiwfn.

    Parameters
    ----------
    path : str
        The path to the .wfn file
    
    Returns
    -------
    str
        Path to the resulting .cub file

    Notes
    -----
    This function is a wrapper around Multiwfn, freely
    available at http://sobereva.com/multiwfn, and 
    published at J. Comput. Chem., 33, 580-592 (2012).
    For this to work, it must be installed and available
    at $PATH.
    """
    batch = b'\n'.join("5 9 2 2".split())
    p = Popen(['Multiwfn', path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.communicate(input=batch)
    os.rename('ELF.cub', '{}.cub'.format(path))
    return '{}.cub'.format(path)