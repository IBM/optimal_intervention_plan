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

import json
from . import data_consts
from .sir_models import (
    SIRModel
)
__can_integrate__ = True
try:
    import scipy.integrate as scint
except ImportError:
    __can_integrate__ = False
    print('aur.resop: "scipy" package not present - integration capability disabled')


class DataFromOpt:
    def __init__(self, data_in, db_connection_url, run_id):
        self._connection_url = db_connection_url
        self._allocated_budget_patches_interventions = self.my_get(data_in, 'allocated_budget_patches_interventions')
        self._allocated_budget_patches = self.my_get(data_in, 'allocated_budget_patches')
        self._coverage_patches_interventions = self.my_get(data_in, 'coverage_patches_interventions')
        self._allocated_budget_interventions = self.my_get(data_in, 'allocated_budget_interventions')
        self._r0 = self.my_get(data_in, 'R0')
        self._base_r0 = self.my_get(data_in, 'base_r0')
        self._objectives = self.my_get(data_in, 'objectives')
        self._coverage_interventions = self.my_get(data_in, 'population_coverage_interventions')
        self._population_coverage_patches_interventions = self.my_get(data_in, 'population_coverage_patches_interventions')
        self._run_id = run_id
        self._patch_ids = self.my_get(data_in, 'patch_ids')
        self._intervention_names = self.my_get(data_in, 'intervention_names')
        self._population = self.my_get(data_in, 'population')
        self._cases = self.get_cases(self._r0)
        self._base_cases = self.get_cases(self._base_r0)
        # TODO - this needs to live in the database and be fed through
        self._fatality = 0.01

    def r0_and_budget_string(self):
        response = ',' + ','.join(self._patch_ids) + '\n'
        response = response + 'r0,' + ','.join(str(x) for x in self._r0) + '\n'
        response = response + 'r0_base,' + ','.join(str(x) for x in self._base_r0) + '\n'
        response = response + 'spend,' + ','.join(str(x) for x in self._allocated_budget_patches) + '\n'
        response = response + 'cases,' + ','.join(str(x) for x in self._cases) + '\n'
        response = response + 'base_cases, ' + ','.join(str(x) for x in self._base_cases) + '\n'
        response = response + 'population, ' + ','.join(str(x) for x in self._population) + '\n'
        return response

    @staticmethod
    def my_get(data, data_value_label):
        if data_value_label not in data:
            raise ValueError('Data from the optimisation should include a value for %s' % data_value_label)
        return data[data_value_label]

    def push_to_database(self):
        raise NotImplementedError('TODO')

    def result_as_json(self):
        result = {
            'id': self._run_id,
            'patches': self.get_patches(),
            'interventions': self.get_interventions(),
            'objectives': self.get_objectives()
        }

        return json.dumps(result)

    def result_as_dict(self):
        result = {
            'id': self._run_id,
            'patches': self.get_patches(),
            'interventions': self.get_interventions(),
            'objectives': self.get_objectives()
        }

        return result

    def get_patches(self):
        result = {}
        for patch in range(len(self._patch_ids)):
            details = []
            for intervention in range(len(self._intervention_names)):
                details.append({
                    'intervention': self._intervention_names[intervention],
                    'coverage': round(self._coverage_patches_interventions[intervention][patch], 2),
                    'populationCoverage': round(self._population_coverage_patches_interventions[intervention][patch]),
                    'totalSpend': round(self._allocated_budget_patches_interventions[intervention][patch])
                })

            patch_dict = {
                'id': data_consts.TRANSFER_NAME_DATA[self._patch_ids[patch]],
                'summary': {
                    'reproductionNumber': round(self._r0[patch], 2),
                    'baseReproductionNumber': round(self._base_r0[patch], 2),
                    'totalSpend': round(self._allocated_budget_patches[patch]),
                    # TODO get these calculating
                    'numCases': round(self._cases[patch]),
                    'baseNumCases': round(self._base_cases[patch]),
                    'numDeaths': round(self._cases[patch] * self._fatality),
                    'baseNumDeaths': round(self._base_cases[patch] * self._fatality)
                },
                'details': details
            }

            result[data_consts.TRANSFER_NAME_DATA[self._patch_ids[patch]]] = patch_dict
        return result

    def get_interventions(self):
        result = []
        for name, budget, coverage in zip(self._intervention_names, self._allocated_budget_interventions,
                                          self._coverage_interventions):
            result.append({
                'intervention': name,
                'totalSpend': round(budget),
                'totalPopulationCoverage': round(coverage)
            })
        return result

    def get_objectives(self):
        return {
            'weightedSum': round(self.my_get(self._objectives, 'weighted_sum')),
            'max': round(self.my_get(self._objectives, 'max_r0'), 2)
        }

    def get_cases(self, r0_vals):
        if __can_integrate__:
            result = []
            for patch in range(len(self._patch_ids)):
                beta = r0_vals[patch]
                gamma = 1
                end_day = 1825  # 5 years
                timespan = range(1, end_day)  # assuming starting at day 1 and time steps of a day and duration in days
                initial_conditions = (self._population[patch] - 1, 1, 0)
                sirmodel = SIRModel(transmission=beta, infectious_period=gamma)
                sirpops = scint.odeint(sirmodel.run, initial_conditions, timespan)

                result.append(sirpops[end_day - 2][2])
            return result
        else:
            print("aur.resop: Warning: Integration disabled - no cases will be reported")
            return [0 for _ in range(len(self._patch_ids))]
