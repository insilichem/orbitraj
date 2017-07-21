#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Documentation here.
"""

from __future__ import print_function, division
import Tkinter as tk
import Pmw
from tkFileDialog import askopenfilenames
from chimera.baseDialog import ModelessDialog
from Movie.gui import MovieDialog

class OrbiTrajDialog(MovieDialog):

    def __init__(self, controller, ensemble, *args, **kwargs):
        self.controller = controller
        MovieDialog.__init__(self, ensemble, *args, **kwargs)
        self.title = "OrbiTraj Movie: " + ensemble.name

    def fillInUI(self, parent):
        self.canvas = parent
        MovieDialog.fillInUI(self, parent)
        self.fileMenu.add_command(label='Add volumes for each frame...',
                                  command=self.add_volumes)
    
    def add_volumes(self, *args, **kwargs):
        paths = askopenfilenames(parent=self.canvas)
        self.controller.add_volumes(paths)


class OrbiTrajConfigDialog(ModelessDialog):

    buttons = ('OK')

    def __init__(self, controller, movie_ui, *args, **kwargs):
        self.title = "OrbiTraj Configuration"
        self.controller = controller
        self.movie_ui = movie_ui
        ModelessDialog.__init__(self, *args, **kwargs)

    def fillInUI(self, parent):
        self.canvas = parent
        self.frame = tk.Frame(self.canvas)
        self.isolevel = Pmw.EntryField(self.frame,
                                       labelpos='w',
                                       label_text='Isosurface value:',
                                       value=self.controller.DEFAULT_ISOLEVEL,
                                       validate={'validator': 'real'},
                                       command=self.update_isolevel)
        self.alpha = Pmw.EntryField(self.frame,
                                    labelpos='w',
                                    label_text='Transparency:',
                                    value=self.controller.DEFAULT_RGBA[-1],
                                    validate={'validator': 'real', 'min': 0, 'max': 1},
                                    command=self.update_alpha)
        self.frame.pack()
        self.isolevel.pack(fill='x', expand=1, padx=10, pady=5)
        self.alpha.pack(fill='x', expand=1, padx=10, pady=5)
        Pmw.alignlabels([self.isolevel, self.alpha])

    def update_isolevel(self, *args, **kwargs):
        isolevel = float(self.isolevel.getvalue())
        self.controller.isosurface(level_2=isolevel)
        for v in self.controller.volumes:
            v.show()
        self.update_alpha()
        print('Updating isolevel to', isolevel)
    
    def update_alpha(self, *args, **kwargs):
        alpha = float(self.alpha.getvalue())
        self.controller.colorize_by_volume(alpha=alpha)
        self.controller.update_volume()
        print('Updating alpha to', alpha)