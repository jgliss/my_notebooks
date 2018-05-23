#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
From 

https://stackoverflow.com/questions/48851880/change-the-order-of-index-in-pandas-dataframe-with-multiindex?rq=1
"""
import pandas as pd
import numpy as np

np.random.seed(2018)
index = pd.MultiIndex(levels=[[u'C', u'D', u'M'], [u'C', u'D', u'M']],
           labels=[[0, 0, 0, 1, 1, 1, 2, 2, 2], [0, 1, 2, 0, 1, 2, 0, 1, 2]],
           names=[u'level0', u'level1'])

df = pd.DataFrame(np.random.randint(10,size=(9,3)),
                  index=index,columns=['C','M','D'])
print (df)

def reindex_order(df, new_order_list, level):
    level_names = df.index.names
    new_levels = []
    for i, name in enumerate(level_names):
        #current unique values of level index
        vals = df.index.get_level_values(name).unique().values
        if name == level or i == level:
            if not len(new_order_list) == len(vals):
                raise ValueError("Mismatch in lengths of input array and "
                                 "index array.")
            elif not all([x in vals for x in new_order_list]):
                raise NameError("Input list is not a permutation of current "
                                "index at level {}".format(level))
            new_levels.append(new_order_list)
        else:
            new_levels.append(vals)
    new_idx = pd.MultiIndex.from_product(new_levels, names=level_names)
    return df.reindex(new_idx)

L = list('CMD')
names = df.index.names
mux = pd.MultiIndex.from_product([L, L], names=names)
df = df.reindex(mux)
print (df)

print(reindex_order(df, list("DCM"), 1))