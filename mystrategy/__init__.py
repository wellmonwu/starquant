#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
dynamically load all strategies in the folder
'''

import os
import importlib
import inspect
strategy_list = {}

path = os.path.abspath(os.path.dirname(__file__))

# loop over all the files in the path
for root, subdirs, files in os.walk(path):
    for name in files:
        # by default, all strategies should end with the word 'strategy'
        if 'strategy' in name and '.pyc' not in name:
            # add module prefix
            moduleName = 'mystrategy.' + name.replace('.py', '')
            # import module
            module = importlib.import_module(moduleName)
            # loop through all the objects in the module and look for the one with 'Strategy' keyword
            for k in dir(module):
                if ('Strategy' in k) and ('StrategyBase' not in k):
                    v = module.__getattribute__(k)
                    strategy_list[k] = v

def strategy_list_reload():
    strategy_list.clear()
    path = os.path.abspath(os.path.dirname(__file__))
# loop over all the files in the path
    for root, subdirs, files in os.walk(path):
        for name in files:
            # by default, all strategies should end with the word 'strategy'
            if 'strategy' in name and '.pyc' not in name:
                # add module prefix
                moduleName = 'mystrategy.' + name.replace('.py', '')
                # import module
                module = importlib.import_module(moduleName)
                # delete old attribute
                for attr in dir(module):
                    if attr not in ('__name__','__file__'):
                        delattr(module,attr)
                importlib.reload(module)
                # loop through all the objects in the module and look for the one with 'Strategy' keyword
                for k in dir(module):
                    if ('Strategy' in k) and ('StrategyBase' not in k):
                        v = module.__getattribute__(k)
                        strategy_list[k] = v