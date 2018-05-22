#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 17:31:42 2018

@author: jonasg
"""

import os 
import pandas
import matplotlib.pyplot as plt

fpath = os.path.join("..", "data", "table_GLBL_ANN_obs.asc")

    
if __name__=="__main__":
    if not os.path.exists(fpath):
        raise IOError("File not found {}".format(fpath))
        
    table = pandas.read_csv(fpath, sep="\s+|\t+|\s+\t+|\t+\s+")
    print(table)
    
    with open(fpath) as f:
        content = []

      
    in_data = True
    for line in lines:
        if line[:8] == "Variable"
    l =lines[10]
    
    spl = l.split("\s+|\t+|\s+\t+|\t+\s+\n")
        
        
    #plt.table(table)    