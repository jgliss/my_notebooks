#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 15:25:24 2019

@author: jonasg
"""

f1 = 'CAM6-Oslo_altRHpiclimaer_od550aer_Column_9999_monthly.nc.csv'
f2 = 'CAM6-Oslo_altRHpiclimaer_od550csaer_Column_9999_monthly.nc.csv'

stats1, stats2 = [], []

with open(f1, 'r') as f:
    for line in f:
        stats1.append(line.split(',')[1])
        
    #data1 = f.readlines()

with open(f2, 'r') as f:
    for line in f:
        stats2.append(line.split(',')[1])
    
print(len(stats1)) 
print(len(stats2)) 

for stat in stats1:
    if not stat in stats2:
        print(stat)
#df2 = pd.read_csv()