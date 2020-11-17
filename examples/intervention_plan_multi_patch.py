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

"""
Example usage of the resource optimization utility

Example usage:
$ python intervention_plan_multi_patch.py --db2_url="jdbc:db2://dashdbon-bluemix.bluemix.net:50000/BLUDB:user=<USERNAME>;password=<PASSWORD>;" \
    --docloud_url="https://api-oaas.docloud.ibmcloud.com/job_manager/rest/v1" \
    --docloud_client_id="<YOUR_CLIENT_ID>"
"""

import argparse
import os.path
import json

from resop.multi_patch_optimizers import InterventionPlanMultiPatch
from resop.data_from_opt import DataFromOpt
from resop.data_manager import DataManager

# Process commandline arguments
parser = argparse.ArgumentParser()

parser.add_argument('--db2_url', help='Db2 JDBC connection url')
parser.add_argument('--docloud_url', help='DOCloud REST API url')
parser.add_argument('--docloud_client_id', help='DOCloud REST API client id')

args = parser.parse_args()

# Construct connected services object
services = {
    'db2': {
        'url': ''
    },
    'docloud': {
        'url': '',
        'client_id': ''
    }
}

# Populate services with values from args
services['db2']['url'] = args.db2_url
services['docloud']['url'] = args.docloud_url
services['docloud']['client_id'] = args.docloud_client_id

PATCH_DATA_FILENAME = 'data/patch_data.json'
RUN_ID = 'test_run_01'

'''
Load patch data from json file...
'''
if os.path.isfile(PATCH_DATA_FILENAME):
    with open(PATCH_DATA_FILENAME) as patch_data_json_data:
        patch_data = json.load(patch_data_json_data)
else:
    '''
    If no patch data JSON file is specified then our data comes from DB2 database
    '''

    # TEST INPUT DATA
    kwargs = {
      'run_id': RUN_ID,
      'country_code': 'TW',
      'country_admin_level': 2,
      'disease_name': 'Dengue',
      'budget_amount': 1000000,
      'intervention_budgets': {}
    }

    # Create the data for input in to the optimisation.
    data_mgr = DataManager(db_connection_url=services['db2']['url'])
    data_mgr.delete_run_by_id(kwargs['run_id'])

    patch_data = data_mgr.create_data(run_id=kwargs['run_id'],
                                      country_code=kwargs['country_code'],
                                      country_admin_level=kwargs['country_admin_level'],
                                      disease_name=kwargs['disease_name'],
                                      budget_amount=kwargs['budget_amount'],
                                      kwargs=kwargs)


'''
Set up the optimiser to run the data
'''
optimiser = InterventionPlanMultiPatch(docloud_url=services['docloud']['url'],
                                       docloud_client_id=services['docloud']['client_id'],
                                       config=patch_data['config'],
                                       patches=patch_data['patches'])

# Run the optimization and get the outputs
result_patch_entry, config_data, result_solved_patch_model = optimiser.run()

# Get optimisation solution
result = InterventionPlanMultiPatch.get_optimization_solution(patches=result_patch_entry,
                                                              config=config_data,
                                                              optimization_model=result_solved_patch_model)

# Transform the result in to the json expected by the application
data_from_opt = DataFromOpt(data_in=result,
                            db_connection_url=None,
                            run_id=RUN_ID)

print(data_from_opt.result_as_dict())

# TODO: Visualize 'result_as_dict()'
