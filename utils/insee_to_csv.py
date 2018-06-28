#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import traceback
import pandas as pd
from toolbox import slashify
from shutil import rmtree

inseeDataPath = slashify(sys.argv[1])
try:
    if os.path.exists(inseeDataPath + 'csv'):
        rmtree(inseeDataPath + 'csv')
    os.mkdir(inseeDataPath + 'csv')

    inseePop09 = pd.read_excel(inseeDataPath + 'BTX_IC_POP_2009.xls', skiprows=(0, 1, 2, 3, 4))
    inseePop09['P09_POP'] = inseePop09['P09_POP'].fillna(0).round().astype(int)
    inseePop09.to_csv(inseeDataPath + 'csv/inseePop09.csv', index=0, columns=['IRIS', 'P09_POP'])

    inseePop12 = pd.read_excel(inseeDataPath + 'base-ic-evol-struct-pop-2012.xls', skiprows=(0, 1, 2, 3, 4))
    inseePop12['P12_POP'] = inseePop12['P12_POP'].fillna(0).round().astype(int)
    inseePop12.to_csv(inseeDataPath + 'csv/inseePop12.csv', index=0, columns=['IRIS', 'P12_POP'])

    inseePop14 = pd.read_excel(inseeDataPath + 'base-ic-evol-struct-pop-2014.xls', skiprows=(0, 1, 2, 3, 4))
    inseePop14['P14_POP'] = inseePop14['P14_POP'].fillna(0).round().astype(int)
    inseePop14.to_csv(inseeDataPath + 'csv/inseePop14.csv', index=0, columns=['IRIS', 'P14_POP'])

    inseeLog14 = pd.read_excel(inseeDataPath + 'base-ic-logement-2014.xls', skiprows=(0, 1, 2, 3, 4))
    inseeLog14['P14_TXRP'] = inseeLog14['P14_RP'] / inseeLog14['P14_LOG']
    inseeLog14.to_csv(inseeDataPath + 'csv/inseeLog14.csv', index=0, columns=['IRIS', 'P14_TXRP'])

except Exception:
    traceback.print_exc(file=sys.stdout)
    sys.exit()