#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import gdal
import time
import numpy as np
import pandas as pd
from shutil import rmtree
from ast import literal_eval

# Ignorer les erreurs de numpy lors d'une division par 0
np.seterr(divide='ignore', invalid='ignore')

# Stockage et contrôle de la validité des paramètres utilisateur
workspacePath = sys.argv[1]
os.chdir(workspacePath)
rate = float(sys.argv[2])
if rate > 3:
    print("Taux d'évolution trop élevé, valeur max acceptée : 3 %")
    sys.exit()
if len(sys.argv) > 3:
    argList = sys.argv[3].split()
    for arg in argList:
        if 'mode' in arg:
            mode = arg.split('=')[1]
            if mode not in {'souple', 'strict'}:
                print("Mode de seuillage invalide \nValeurs possibles : souple ou strict")
                sys.exit()
        if 'saturateFirst' in arg:
            saturateFirst = literal_eval(arg.split('=')[1])
        if 'pluPriority' in arg:
            pluPriority = literal_eval(arg.split('=')[1])
        if 'finalYear' in arg:
            finalYear = int(arg.split('=')[1])

# Valeurs de paramètres par défaut
if 'mode' not in globals():
    mode = 'souple'
if 'saturateFirst' not in globals():
    saturateFirst = True
if 'pluPriority' not in globals():
    pluPriority = True
if 'finalYear' not in globals():
    finalYear = 2040

projectPath = mode + '_' + str(rate) + '/'
if os.path.exists(projectPath):
    rmtree(projectPath)
os.mkdir(projectPath)
os.mkdir(projectPath + '/snapshots')

res = re.search('.*/([0-9]*)m+', workspacePath)
cellSurf = int(res.group(1)) * int(res.group(1))

# Création d'un fichier journal
log = open(projectPath + 'log.txt', 'x')

# Convertit un tif en numpy array
def to_array(tif, dtype=None):
    ds = gdal.Open(tif)
    if dtype == 'float32':
        return ds.ReadAsArray().astype(np.float32)
    elif dtype == 'uint16':
        return ds.ReadAsArray().astype(np.uint16)
    else:
        return ds.ReadAsArray()
    ds = None

# Enregistre un fichier .tif à partir d'un array et de variables GDAL stockée au préalable
def to_tif(array, dtype, path):
    ds_out = driver.Create(path, cols, rows, 1, dtype)
    ds_out.SetProjection(proj)
    ds_out.SetGeoTransform(geot)
    ds_out.GetRasterBand(1).WriteArray(array)
    ds_out = None

# Fonction de répartition de la population
def urbanize(mode, popALoger, saturateFirst=True, pluPriority=False):
    global population, capacite
    popLogee = 0
    capaciteTmp = capacite.copy()
    populationTmp = np.zeros([rows, cols], np.uint16)

    if mode == 'souple':
        if saturateFirst:
            capaciteTmp = np.where(population > 0, capaciteTmp, 0)
        if pluPriority:
            capaciteTmp = np.where(plu_priorite == 1, capaciteTmp, 0)
        while popLogee < popALoger and capaciteTmp.sum() > 0:
            weight = np.where(capaciteTmp > 0, interet, 0)
            flatWeight = weight.flatten()
            choices = np.random.choice(flatWeight.size, popALoger - popLogee, p=flatWeight / flatWeight.sum())
            i = 0
            while i < choices.size :
                row = choices[i] // weight.shape[1]
                col = choices[i] % weight.shape[1]
                if capaciteTmp[row][col] > 0:
                    populationTmp[row][col] += 1
                    popLogee += 1
                    capaciteTmp[row][col] -= 1
                i += 1
        # Si on a pas pu loger tout le monde dans des cellules déjà urbanisées => expansion
        if saturateFirst and popALoger - popLogee > 0:
            capaciteTmp = np.where(population == 0, capacite - populationTmp, 0)
            if pluPriority:
                capaciteTmp = np.where(plu_priorite == 1, capaciteTmp, 0)
            while popLogee < popALoger and capaciteTmp.sum() > 0:
                weight = np.where(capaciteTmp > 0, interet, 0)
                flatWeight = weight.flatten()
                choices = np.random.choice(flatWeight.size, popALoger - popLogee, p=flatWeight / flatWeight.sum())
                i = 0
                while i < choices.size :
                    row = choices[i] // weight.shape[1]
                    col = choices[i] % weight.shape[1]
                    if capaciteTmp[row][col] > 0:
                        populationTmp[row][col] += 1
                        popLogee += 1
                        capaciteTmp[row][col] -= 1
                    i += 1

    elif mode == 'strict':
        if pluPriority:
            capaciteTmp = np.where(plu_priorite == 1, capaciteTmp, 0)
        while popLogee < popALoger and capaciteTmp.sum() > 0:
            i = 0
            weight = np.where(capaciteTmp > 0, interet, 0)
            flatWeight = weight.flatten()
            choices = np.random.choice(flatWeight.size, popALoger - popLogee, p=flatWeight / flatWeight.sum())
            while i < choices.size:
                row = choices[i] // weight.shape[1]
                col = choices[i] % weight.shape[1]
                if capaciteTmp[row][col] > 0:
                    cellCapa = capaciteTmp[row][col]
                    if cellCapa <= popALoger - popLogee:
                        populationTmp[row][col] += cellCapa
                        popLogee += cellCapa
                        capaciteTmp[row][col] -= cellCapa
                    else:
                        cellCapa = cellCapa - (cellCapa - (popALoger - popLogee))
                        populationTmp[row][col] += cellCapa
                        popLogee += cellCapa
                        capaciteTmp[row][col] -= cellCapa
                i += 1

    capacite -= populationTmp
    population = population + populationTmp
    to_tif(population, gdal.GDT_UInt16, projectPath + 'snapshots/pop_' + str(year) + '.tif')
    return popALoger - popLogee

start_time = time.time()
print("Commencé à " + time.strftime('%H:%M:%S'))

# Création des dataframes contenant les informations par IRIS
irisDf = pd.read_csv('iris.csv')
pop = sum(irisDf['population'])
dicPop = {}
year = 2015
while year <= finalYear:
    if year == 2015:
        dicPop[year] = int(sum(irisDf['population']) * (rate / 100))
        pop += int(sum(irisDf['population']) * (rate / 100))
    else:
        dicPop[year] = int(pop * (rate / 100))
        pop += int(pop * (rate / 100))
    year += 1

sumPopALoger = sum(dicPop.values())
# Nombre total de personnes à loger - permet de vérifier si le raster capacité permet d'accueillir tout le monde
dfPop = pd.DataFrame.from_dict(dicPop, orient='index')
dfPop.to_csv(projectPath + 'projections.csv')
log.write("Population à loger d'ici à " +
          str(finalYear) + ", " + str(sumPopALoger) + "\n")

# Calcul des coefficients de pondération de chaque raster d'intérêt, csv des poids dans le répertoire des données locales
poids = pd.read_csv('poids.csv')
poids['coef'] = poids['poids'] / sum(poids['poids'])
poids.to_csv(projectPath + 'coefficients.csv', index=0)
dicCoef = {row[0]: row[2] for _, row in poids.iterrows()}
del poids

# Création des variables GDAL pour écriture de raster, indispensables pour la fonction to_tif()
ds = gdal.Open('population.tif')
population = ds.GetRasterBand(1).ReadAsArray().astype(np.uint16)
cols = ds.RasterXSize
rows = ds.RasterYSize
proj = ds.GetProjection()
geot = ds.GetGeoTransform()
driver = gdal.GetDriverByName('GTiff')
ds = None

# Préparation du raster de capacité, nettoyage des cellules interdites à la construction
restriction = to_array('restriction.tif')
capacite = to_array('capacite.tif', 'uint16')
to_tif(capacite, gdal.GDT_UInt16, 'capa2.tif')
capacite = np.where(restriction != 1, capacite, 0)
if os.path.exists('plu_restriction.tif') and os.path.exists('plu_priorite.tif'):
    hasPlu = True
    plu_priorite = to_array('plu_priorite.tif')
    plu_restriction = to_array('plu_restriction.tif')
    capacite = np.where(plu_restriction != 1, capacite, 0)
else:
    hasPlu = False

# On vérifie que la capcité d'accueil est suffisante, ici on pourrait modifier la couche de restriction pour augmenter la capacité
f = 0
capaciteAccueil = np.sum(capacite)
log.write("Capacité d'accueil originale du territoire, " + str(capaciteAccueil) + '\n')
if capaciteAccueil < sumPopALoger:
    f += 100
    if hasPlu:
        print("La capacité d'accueil étant insuffisante, on retire les restrictions issues du PLU.")
        capacite = to_array('capacite.tif', 'uint16')
        capacite = np.where(restriction != 1, capacite, 0)
        capaciteAccueil = np.sum(capacite)
        if capaciteAccueil < sumPopALoger:
            while capaciteAccueil < sumPopALoger:
                f += 5
                capacite = to_array('capacite.tif', 'uint16')
                capacite = np.where(restriction != 1, capacite, 0)
                capacite = capacite * (f/100)
                capaciteAccueil = np.sum(capacite)
            print("Afin de loger tout le monde, la capacite est augmentée de " + str(f) + ' %')
    # Ici on augmente les valeurs du raster de capacité avec un pas de 5 %
    else:
        while capaciteAccueil < sumPopALoger:
            f += 5
            print("Capacite  " + str(f) + ' %')
            capacite = to_array('capacite.tif', 'uint16')
            capacite = np.where(restriction != 1, capacite, 0)
            capacite = capacite * (f/100)
            capaciteAccueil = np.sum(capacite)
        print("Afin de loger tout le monde, la capacite est augmentée de " + str(f) + ' %')

log.write("Pourcentage d'augmentation de la capacite, " + str(f) + "\n")
log.write("Nouvelle capacité d'accueil du territoire, " + str(capaciteAccueil) + "\n")
capaciteDepart = capacite.copy()
populationDepart = population.copy()

# Conversion des autres raster d'entrée en numpy array
iris = to_array('iris_id.tif', 'uint16')
ecologie = to_array('ecologie.tif', 'float32')
ocsol = to_array('ocsol.tif', 'float32')
routes = to_array('routes.tif', 'float32')
transport = to_array('transport.tif', 'float32')
sirene = to_array('sirene.tif', 'float32')

# Création du raster final d'intérêt avec pondération
interet = np.where((restriction != 1), (ecologie * dicCoef['ecologie']) + (ocsol * dicCoef['ocsol']) + (routes * dicCoef['routes']) + (transport * dicCoef['transport']) + (
    sirene * dicCoef['sirene']), 0)
to_tif(interet, gdal.GDT_Float32, projectPath + 'interet.tif')
del dicCoef, restriction, ocsol, routes, transport, sirene

for year in range(2015, finalYear + 1):
    print(str(year))
    popALoger = dicPop[year]
    if hasPlu:
        popRestante = urbanize(mode, popALoger, saturateFirst, pluPriority)
        if popRestante > 0:
            reste=urbanize(mode, popRestante, saturateFirst)
    else:
        urbanize(mode, popALoger, saturateFirst)

# Calcul et export des résultats
popNouvelle = population - populationDepart
capaSaturee = np.where((capaciteDepart > 0) & (capacite == 0), 1, 0)
expansion = np.where((populationDepart == 0) & (population > 0), 1, 0)
peuplementMoyen = np.nanmean(np.where(popNouvelle == 0, np.nan, popNouvelle))
impactEnvironnemental = np.where(expansion == 1, 1 - ecologie, 0).sum() * cellSurf
expansionSum = expansion.sum() * cellSurf

to_tif(capacite, gdal.GDT_UInt16, projectPath + 'capacite_future.tif')
to_tif(population, gdal.GDT_UInt16, projectPath + 'population_future.tif')
to_tif(expansion, gdal.GDT_Byte, projectPath + 'expansion.tif')
to_tif(popNouvelle, gdal.GDT_UInt16, projectPath + 'population_nouvelle.tif')
to_tif(capaSaturee, gdal.GDT_Byte, projectPath + 'capacite_saturee')

log.write("Expansion totale en m2, " + str(expansionSum) + "\n")
log.write("Peuplement moyen des cellules, " + str(peuplementMoyen) + "\n")
log.write("Impact environnemental cumulé, " + str(impactEnvironnemental) + "\n")
log.write("Temps d'execution, " + str(round(time.time() - start_time, 2)))
print('Terminé  à ' + time.strftime('%H:%M:%S'))
