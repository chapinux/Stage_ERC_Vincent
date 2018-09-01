#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import csv
import numpy as np
import matplotlib.pylab as plt

def slashify(path):
    if path[len(path)-1] != '/':
        return path + '/'
    else:
        return path

directory = slashify(sys.argv[1])
outdir = slashify(sys.argv[2])
if len(sys.argv) > 3:
    nbIris = int(sys.argv[3])
else:
    nbIris = 160

if not os.path.exists(outdir):
    os.makedirs(outdir)

os.mkdir(outdir + 'floors')
os.mkdir(outdir + 'surf')

def parseDistrib(file, type=None, fit=True, fitIndicator=None):
    poids = {}
    for i in range(nbIris):
        poids[i+1] = {}
    file.readline()
    for l in file.readlines():
        values = l.split(',')
        if fit:
            if type == 'floors':
                id = int(values[1].replace('"',''))
                etages = int(values[2].replace('"',''))
                if fitIndicator == 'AIC':
                    f = 4
                elif fitIndicator == 'Chi2':
                    f = 5

                poids[id][etages] = float(values[f].replace('\n','')) if 'NA' not in values[f] else 0

            elif type == 'surf':
                if fitIndicator == 'AIC':
                    f = 5
                elif fitIndicator == 'KS':
                    f = 4
                elif fitIndicator == 'CVM':
                    f = 3
                elif fitIndicator == 'AD':
                    f = 2

                id = int(values[6].replace('"','').replace('\n',''))
                surf = float(values[1])
                poids[id][surf] = float(values[f])

        else:
            id = int(values[0])
            dist = int(values[1])
            poids[id][dist] = float(values[3])
    return poids


with open(directory + 'poids_etages.csv') as r:
    poidsEtagesAIC = parseDistrib(r, 'floors', fitIndicator = 'AIC')
with open(directory + 'poids_etages.csv') as r:
    poidsEtagesChi2 = parseDistrib(r, 'floors', fitIndicator = 'Chi2')

with open(directory  + 'poids_surfaces.csv') as r:
    poidsSurfacesAIC = parseDistrib(r, 'surf', fitIndicator = 'AIC')
with open(directory  + 'poids_surfaces.csv') as r:
    poidsSurfacesKS = parseDistrib(r, 'surf', fitIndicator = 'KS')
with open(directory  + 'poids_surfaces.csv') as r:
    poidsSurfacesCVM = parseDistrib(r, 'surf', fitIndicator = 'CVM')
with open(directory  + 'poids_surfaces.csv') as r:
    poidsSurfacesAD = parseDistrib(r, 'surf', fitIndicator = 'AD')

with open(directory  + 'poids_etages_nofit.csv') as r:
    poidsEtagesNoFit = parseDistrib(r, fit = False)

with open(directory + 'poids_surfaces_nofit.csv') as r:
    poidsSurfacesNoFit = parseDistrib(r, fit=False)

for i in range(nbIris):
    plt.xlabel('Nombre de niveaux')
    plt.ylabel('Poids du nombre de niveaux dans la distribution')

    fN = tuple(poidsEtagesNoFit[i+1].keys())
    pN = tuple(poidsEtagesNoFit[i+1].values())
    fF = tuple(poidsEtagesAIC[i+1].keys())
    pFA = tuple(poidsEtagesAIC[i+1].values())
    pFC = tuple(poidsEtagesChi2[i+1].values())

    plt.plot(fN, pN, 'g', label='Distribution existante', marker='o', linewidth=1)
    plt.plot(fF, pFA, 'r', label='Critère AIC', linewidth=1)
    plt.plot(fF, pFC, 'b', label='Critère Chi2', linewidth=1)
    plt.legend()
    plt.savefig(outdir + 'floors/IRIS_n' + str(i+1) + '.png')
    plt.close()

for i in range(nbIris):
    plt.xlabel('Surface au sol')
    plt.ylabel('Poids de la surface dans la distribution')

    sN = tuple(poidsSurfacesNoFit[i+1].keys())
    pN = tuple(poidsSurfacesNoFit[i+1].values())
    sF = tuple(poidsSurfacesAIC[i+1].keys())
    pFA = tuple(poidsSurfacesAIC[i+1].values())
    pFKS = tuple(poidsSurfacesKS[i+1].values())
    pFC = tuple(poidsSurfacesCVM[i+1].values())
    pFAD = tuple(poidsSurfacesAD[i+1].values())

    plt.plot(sN, pN, 'g', label='Distribution existante', linewidth=1)
    plt.plot(sF, pFA, 'r', label= 'Critère AIC', linewidth=1)
    plt.plot(sF, pFKS, 'b', label= 'Critère KS', linewidth=1)
    plt.plot(sF, pFC, 'm', label= 'Critère CVM', linewidth=1)
    plt.plot(sF, pFAD, 'c', label= 'Critère AD', linewidth=1)
    plt.legend()
    plt.savefig(outdir + 'surf/IRIS_n' + str(i+1) + '.png')
    plt.close()

print('Done...')
