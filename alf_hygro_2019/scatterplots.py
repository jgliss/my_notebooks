#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 11:27:50 2019

@author: jonasg
"""

import os
import pyaerocom as pya
import matplotlib.pyplot as plt


OUT_DIR = './output/'

MODEL_IDS = ['CAM6-Oslo_NF1850norbc_aer2014_f19_20190727',
             'CAM6-Oslo_altRHpiclimaer']

VARS = ['od550aer', 'od550csaer']

START = 2014
TS_TYPE = 'monthly'
FILTER_NAME = 'WORLD-noMOUNTAINS'

OBS_ID = 'AeronetSunV3Lev2.daily'


if __name__ == '__main__':
    plt.close('all')   
    
    
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)
    
    coldata = {}
    
    colocator = pya.Colocator(obs_id=OBS_ID, 
                              obs_vars='od550aer', 
                              ts_type=TS_TYPE, 
                              start=START,
                              filter_name=FILTER_NAME,
                              remove_outliers=False,
                              model_add_vars={'od550aer':'od550csaer'}, 
                              save_coldata=False,
                              model_use_climatology=True)
    for model_id in MODEL_IDS:
        colocator.run(model_id=model_id)
            
            

    for mid, vardict in colocator.data.items():
        for var_name, coldata in vardict.items():
            coldata.rename_variable('od550aer', var_name, data_source=mid)
            ax = coldata.plot_scatter()
            
            fpath = OUT_DIR + '{}_{}.png'.format(mid, var_name)
            ax.figure.savefig(fpath)
    
    
        
    
    CONT = False
    if CONT:
        start, stop = pya.helpers.start_stop_from_year(START)
        
        obsdata = pya.io.ReadUngridded().read(OBS_ID, 'od550aer')
        
        stats = obsdata.to_station_data_all('od550aer', 
                                            start=start, stop=stop, 
                                            freq=TS_TYPE)
        
        
        print(1, len(stats['station_name']), len(stats['stats']))
        
        f = pya.Filter(FILTER_NAME)
        
        obsdata = f(obsdata)
        
        stats = obsdata.to_station_data_all('od550aer', 
                                            start=start, stop=stop, 
                                            freq=TS_TYPE)
        
        print(2, len(stats['station_name']), len(stats['stats']))
        
        obsdata = f(obsdata)
        
        stats = obsdata.to_station_data_all('od550aer', 
                                            start=start, stop=stop, 
                                            freq=TS_TYPE)
        
        print(2.1, len(stats['station_name']), len(stats['stats']))
        
        obsdata.remove_outliers('od550aer', inplace=True)
        
        stats = obsdata.to_station_data_all('od550aer', 
                                            start=start, stop=stop, 
                                            freq=TS_TYPE)
        
        print(3, len(stats['station_name']), len(stats['stats']))
        
        obsdata.remove_outliers('od550aer', inplace=True)
        
        stats = obsdata.to_station_data_all('od550aer', 
                                            start=start, stop=stop, 
                                            freq=TS_TYPE)
        
        print(3.1, len(stats['station_name']), len(stats['stats']))