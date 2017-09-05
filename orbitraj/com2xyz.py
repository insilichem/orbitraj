#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Converts a Gaussian .com file into simple XYZ coordinates.
"""
# Stdlib
import sys

def gaussiancom_to_xyz(path):
    atoms = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            elif line.startswith('#'):  # actual contents begin
                for i in range(5):
                    line = next(f)
                line = line.strip()
                while line:
                    fields = line.split()
                    atoms.append(' '.join(fields[:4]))
                    line = next(f).strip()
                break
    return '\n'.join(atoms)

if __name__ == '__main__':
    paths = sys.argv[1:]
    for path in paths:
        with open(path + '.xyz', 'w') as f:
            f.write(gaussiancom_to_xyz(path))