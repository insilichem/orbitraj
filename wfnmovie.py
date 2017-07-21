#!/usr/bin/env pychimera
# -*- coding: utf-8 -*-

"""
Generate a mkv movie from wfn files.

Usage
-----
Usage: python2 wfnmovie.py '<files>' [create_movie]

    <files>      : quoted glob expression like "*.wfn"
    create_movie : If True, convert & render movie. Must be
                   executed with pychimera, instead of python2.
                   If False to only  convert files (optional,
                   default=True). The conversion process 
                   will create both cub and pdb files.

Requirements
------------
- Python 2.7
- Multiwfn (http://sobereva.com/multiwfn/)

If you want to render movies:
- UCSF Chimera headless (https://www.cgl.ucsf.edu/chimera/)
- PyChimera (https://github.com/insilichem/pychimera)
- ffmpeg
- tqdm (https://pypi.python.org/pypi/tqdm; optional)
"""

from __future__ import print_function, division
import sys
import os
from glob import glob
from subprocess import Popen, PIPE, STDOUT
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda a: a


def generate_wfn(wfn):
    print('Generating .cub and .pdb files for {} wfn files'.format(len(wfn)))
    batch = b'\n'.join("5 9 2 2 0 100 2 1 some.pdb".split())
    for f in tqdm(wfn):
        p = Popen(['Multiwfn', f], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p.communicate(input=batch)
        os.rename('ELF.cub', '{}.cub'.format(f))
        os.rename('some.pdb', '{}.pdb'.format(f))


def generate_images(cubs, pdbs):
    if 'CHIMERA' not in os.environ:
        sys.exit("To render movies, you must run the script with "
                 "pychimera: pychimera wfnmovie.py [...]")
    from chimera import runCommand as rc, openModels
    print('Generating .png images for {} cub/pdb files'.format(len(cubs)))
    for i, (cub, pdb) in tqdm(enumerate(zip(cubs, pdbs))):
        cubmodel = openModels.open(cub)[0]
        pdbmodel = openModels.open(pdb)[0]
        rc('vol #0 level 0.70')
        rc('scolor #0 gradient #0 cmap rainbow')
        rc('transp 50 #0')
        rc('turn y 180')
        rc('turn x -60')
        rc('focus')
        rc('copy file {}.png width 1280 height 720'.format(cub.split('.')[0]))
        openModels.close([cubmodel, pdbmodel])


def generate_movie(images, output='output.mkv'):
    print('Generating movie...')
    os.system('rm {1}; cat {0} | ffmpeg -framerate 2 -f image2pipe -i - {1}'.format(images, output))


def main():
    generate_wfn(glob(sys.argv[1]))
    if len(sys.argv) == 3 and bool(sys.argv[2]):
        generate_images(sorted(glob('*.cub')), sorted(glob('*.pdb')))
        generate_movie('*.png', output='output.mkv')
    

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3) or sys.argv[1] == '-h':
        sys.exit(__doc__)
    main()