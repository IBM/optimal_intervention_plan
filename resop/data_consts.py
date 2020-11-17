#!/usr/bin/env python

##################################################################
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
##################################################################

# TABLE_NAMES
TBL_GEOGRAPHIES = 'GEOGRAPHIES'
TBL_PATCHES = 'PATCHES'
TBL_DISEASES = 'DISEASES'
TBL_INTERVENTIONS = 'INTERVENTIONS'
TBL_DISEASE_PARAMS = 'DISEASE_PARAMS'
TBL_DISEASE_PATCH_PARAMS = 'DISEASE_PATCH_PARAMS'
TBL_INTERVENTION_PATCH_PARAMS = 'INTERVENTION_PATCH_PARAMS'
TBL_INTERVENTION_COST_BREAKPOINTS = 'INTERVENTION_COST_BREAKPOINTS'
TBL_RUNS = 'RUNS'
TBL_PATCH_BUDGETS = 'PATCH_BUDGETS'
TBL_INTERVENTION_BUDGETS = 'INTERVENTION_BUDGETS'
TBL_RESULTS_INTERVENTIONS = 'RESULTS_INTERVENTIONS'
TBL_RESULTS = 'RESULTS'

TRANSFER_NAME_DATA = {
    'TW.FK.LK': 'TW.NA.NA',
    'TW.FK.KM': 'TW.TW.PH',
    'TW.TA.PH': 'TW.TW.TT',
    'TW.TA.TT': 'TW.TW.CH',
    'TW.TA.CS': 'TW.TW.HL',
    'TW.TA.HL': 'TW.TW.CL',
    'TW.TA.CL': 'TW.TW.HH',
    'TW.TA.IL': 'TW.TW.IL',
    'TW.TA.NT': 'TW.TW.NT',
    'TW.TA.HS': 'TW.TW.ML',
    'TW.TA.CH': 'TW.TW.YL',
    'TW.TA.HH': 'TW.TW.PT',
    'TW.TA.ML': 'TW.TW.CG',
    'TW.TA.YL': 'TW.TW.TA',
    'TW.TA.PT': 'TW.TW.TN',
    'TW.TA.CG': 'TW.TW.TY',
    'TW.TN.TI': 'TW.TP.TC',
    'TW.TA.TY': 'TW.TW.TP',
    'TW.TP.TC': 'TW.TW.TH',
    'TW.TG.TU': 'TW.TW.TG',
    'TW.KH.KS': 'TW.KH.KC',
    'TW.NT.TP': 'TW.TW.KH'
}
