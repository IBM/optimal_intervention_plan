#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
Created on Tue Jul 18 11:12:23 2017

@author: Hamideh Anjomshoa
@author: Stefan von Cavallar
"""

# Python 2 and 3 support
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from future.utils import raise_with_traceback
from docplex.mp.model import Model
import numpy as np


class InterventionPlanMultiPatch(object):
    def __init__(self, docloud_url, docloud_client_id, config, patches):
        """
        Class constructor

        :param docloud_url: DOCloud REST API endpoint url
        :param docloud_client_id: DOCloud REST API client id/key
        :param config: object containing global configuration values
        :param patches: Array of patch entries
        """
        self.name = None

        self._docloud_url = docloud_url
        self._docloud_client_id = docloud_client_id

        self.config = config

        assert patches and len(patches) > 0

        self.patches = patches

    def __str__(self):
        """
        Return the optimization name
        """
        if self.name is not None:
            return self.name
        else:
            return self.__class__.__name__

    def run(self):
        """

        :return: The patch entry and its associated optimization solution
        """

        patches, config, patch_model = self.build_model()

        # Run the solver on this patch model
        if not patch_model.solve(url=self._docloud_url, key=self._docloud_client_id):
            raise_with_traceback(ValueError('Error solving model'))

        return patches, config, patch_model

    def build_model(self):
        """
        Builds an optimization model for the specified patch entry

        :return:
        """

        '''
        Convert data to optimisation data
        '''
        population = []
        beta = []
        gamma = []
        minimum_patch_budget = []
        threshold_coverage =[]
        threshold_cost =[]
        efficacy_beta = []
        efficacy_gamma = []

        for patch in self.patches.keys():
            population.append(self.patches[patch]['population'])
            beta.append(self.patches[patch]['Beta'])
            gamma.append(self.patches[patch]['Gamma'])
            minimum_patch_budget.append(self.patches[patch]['minimum_patch_budget'])
            threshold_coverage.append(self.patches[patch]['threshold_coverage'])
            threshold_cost.append(self.patches[patch]['threshold_costs'])
            efficacy_beta.append(self.patches[patch]['efficacyBeta'])
            efficacy_gamma.append(self.patches[patch]['efficacyGamma'])

        for x in range(1, 8):
            beta[2*x]=beta[2*x] + 0.5
            gamma[3*x] = gamma[3*x]-1
        print("beta = ", beta)
        print("gamma", gamma)
        print("R0-initials = ", np.multiply(beta, gamma))
        print("efficacy_beta", efficacy_beta)
        print("efficacy-gamma", efficacy_gamma)
        print("population", population)
        print("threshold cost", threshold_cost)


        num_patches = len(self.patches)
        num_phases = len(threshold_coverage[0])
        num_interventions = self.config['num_interventions']
        num_pieces = self.config['num_pieces']
        total_budget = self.config['total_budget']


        minimim_intervention_budget= self.config['minimum_intervention_budget']
        maximum_intervention_budget = self.config['maximum_intervention_budget']

        '''
        Optimisation Model
        '''

        model = Model('test_optimizer')

        '''
        Decision Variables
        '''
        c_points = [[[] for p in range(0, num_patches)] for i in range(0, num_interventions)]
        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                for j in range(0, num_pieces+1):
                    c_points[i][p].append(j / num_pieces)

        # Threshold indices are  p i k #
        y_points = [[[] for i in range(0, num_interventions)] for p in range(0, num_patches)]
        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                y_points[p][i].append(0)
                for k in range(1, num_phases):
                    y_points[p][i].append(y_points[p][i][k-1] + threshold_cost[p][i][k] *(threshold_coverage[p][i][k] - threshold_coverage[p][i][k-1]))

        model.cover_var= [[] for i in range(0, num_interventions)]
        model.total_dollar_var = [[] for i in range(0, num_interventions)]
        model.alpha_var = [[] for i in range(0, num_interventions)]

        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                model.cover_var[i].append( model.continuous_var(lb=0, ub=1, name='cover%d_%d' % (i, p)))
                model.total_dollar_var[i].append(model.continuous_var(lb=0, ub=total_budget, name='total_dollar%d_%d' % (i, p)))
                model.alpha_var[i].append(model.binary_var(name='alpha%d_%d' % (i, p)))

        model.var_R0 = [model.continuous_var(lb=np.log(0.9) - np.log(beta[p] * gamma[p]), name='R0' + str(p)) for p in range(0, num_patches)]

        model.w_var = [[[] for p in range(0, num_patches)]for i in range(0, num_interventions)]
        model.lambda_var = [[[] for p in range(0, num_patches)] for i in range(0, num_interventions)]
        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                for j in range(0, num_pieces+1):
                    model.w_var[i][p].append(model.continuous_var(lb =0, ub =1, name= 'w%d_%d_%d' %(i, p, j)))
                    model.lambda_var[i][p].append(model.binary_var( name='lambda_%d_%d_%d' %(i, p, j)))

        model.eta_var = [[[] for p in range(0, num_patches)]for i in range(0, num_interventions)]
        model.psi_var = [[[] for p in range(0, num_patches)] for i in range(0, num_interventions)]
        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                for k in range(0, num_phases):
                    model.eta_var[i][p].append(model.continuous_var(lb=0, ub=1, name= 'eta%d_%d_%d' % (i, p, k)))
                    model.psi_var[i][p].append(model.binary_var(name='psi%d_%d_%d' % (i, p, k)))

        '''
        Constraints
        '''
        # budget  constraints

        model.add_constraint(model.sum(model.total_dollar_var[i][p] for i in range(0, num_interventions) for p in range(0, num_patches)) <= total_budget)
        model.add_constraints(model.sum(model.total_dollar_var[i][p] for i in range(0, num_interventions)) >= minimum_patch_budget[p] for p in range(0, num_patches))
        model.add_constraints(model.sum(model.total_dollar_var[i][p] for p in range(0, num_patches)) >= minimim_intervention_budget[i] for i in range(0,num_interventions))
        model.add_constraints(model.sum(model.total_dollar_var[i][p] for p in range(0, num_patches)) <= maximum_intervention_budget[i] for i in range(0, num_interventions))

        # objective piecewise linear constraints

        model.add_constraints(model.sum(model.w_var[i][p][j] for j in range(0, num_pieces+1)) == 1 for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.sum(c_points[i][p][j] * model.w_var[i][p][j] for j in range(0, num_pieces+1)) == model.cover_var[i][p] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.sum(model.lambda_var[i][p][j] for j in range(1, num_pieces+1)) == 1 for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.w_var[i][p][0] <= model.lambda_var[i][p][1] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.w_var[i][p][num_pieces] <= model.lambda_var[i][p][num_pieces] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.w_var[i][p][j] <= model.lambda_var[i][p][j] + model.lambda_var[i][p][j+1] for i in range(0, num_interventions) for p in range(0, num_patches) for j in range(1, num_pieces))

        model.add_constraints(model.sum((np.log(1-float(efficacy_beta[p][i] * c_points[i][p][j])) +
                                        np.log(1-float(efficacy_gamma[p][i] * c_points[i][p][j]))) * model.w_var[i][p][j]
                                        for i in range(0, num_interventions) for j in range(0, num_pieces+1))
                              == model.var_R0[p] for p in range(0,num_patches))

        # cost piecewise linear constraints
        model.add_constraints(model.sum(model.eta_var[i][p][k] * threshold_coverage[p][i][k] for k in range(0, num_phases) ) == model.cover_var[i][p] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.sum(model.eta_var[i][p][k] * threshold_cost[p][i][k] for k in range(0, num_phases)) + model.alpha_var[i][p] * threshold_cost[p][i][0]  == model.total_dollar_var[i][p] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.sum(model.eta_var[i][p][k] for k in range(0, num_phases)) == 1 for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.sum(model.psi_var[i][p][k] for k in range(0, num_phases)) == 1 for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.eta_var[i][p][0] <= model.psi_var[i][p][0] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.eta_var[i][p][num_phases-1] <= model.psi_var[i][p][num_phases-2] for i in range(0, num_interventions) for p in range(0, num_patches))
        model.add_constraints(model.eta_var[i][p][k] <= model.psi_var[i][p][k-1] + model.psi_var[i][p][k] for i in range(0, num_interventions) for p in range(0, num_patches) for k in range(1, num_phases-1))

        # for the presentation only
        min_r0_possible = np.log(0.9) - np.log(beta[0]*gamma[0])

        model.max_var = model.continuous_var(lb=min_r0_possible, name="max_var")
        model.add_constraints(model.max_var >= model.var_R0[p] for p in range(0, num_patches))

        '''
        Objective
        '''
        model.minimize(model.sum(population[p] * (model.var_R0[p] + model.max_var) for p in range(0, num_patches)))
        return self.patches, self.config, model
        # return patch_entry, model

    @staticmethod
    def get_optimization_solution(patches, config, optimization_model):
        """
        Utility function for printing the solution details for the specified optimization model

        :param patches: List pf patches and all related information
        :param config: Global data
        :param optimization_model: Optimization model solution returned from build_patch_model
        :return:
        """

        num_interventions = config['num_interventions']
        num_patches = len(patches)
        total_budget = config['total_budget']
        population = []
        beta = []
        gamma =[]
        patch_ids = []

        for patch in patches.keys():
            population.append(patches[patch]['population'])
            beta.append(patches[patch]['Beta'])
            gamma.append(patches[patch]['Gamma'])
            patch_ids.append(patches[patch]['name'])

        solution_allocated_budget_patches_interventions =[[] for i in range(0, num_interventions)]
        solution_allocated_budget_patches = np.zeros(num_patches)
        solution_allocated_budget_interventions = np.zeros(num_interventions)
        solution_coverage_patches_interventions = [[] for i in range(0, num_interventions)]
        solution_population_coverage_interventions = np.zeros(num_interventions)
        solution_population_coverage_patches_interventions = [[] for _ in range(num_interventions)]
        solution_r0 = []
        base_r0 = []

        for i in range(0, num_interventions):
            for p in range(0, num_patches):
                solution_allocated_budget_patches_interventions[i].append(optimization_model.total_dollar_var[i][p].solution_value)
                solution_allocated_budget_patches[p] = solution_allocated_budget_patches[p] +  optimization_model.total_dollar_var[i][p].solution_value
                solution_coverage_patches_interventions[i].append(optimization_model.cover_var[i][p].solution_value)
                solution_population_coverage_interventions[i]= solution_population_coverage_interventions[i]+ optimization_model.cover_var[i][p].solution_value *population[p]
                solution_population_coverage_patches_interventions[i].append(optimization_model.cover_var[i][p].solution_value * population[p])
            solution_allocated_budget_interventions[i] = np.sum(solution_allocated_budget_patches_interventions[i][:])

        weighted_sum = 0
        max_r0 = -np.infty
        for p in range(0, num_patches):
            r_value = np.exp(np.log(beta[p] * gamma[p]) + optimization_model.var_R0[p].solution_value)
            base_r0.append(np.exp(np.log(beta[p] * gamma[p])))
            solution_r0.append(r_value)
            if max_r0 < r_value:
                max_r0 = r_value
            weighted_sum += population[p] * r_value

        print('R0 = ', solution_r0)
        print('maxR0 = ', np.max(solution_r0))
        print('budget allocated to each patch = ', solution_allocated_budget_patches)
        print('budget allocated to each interventions =', solution_allocated_budget_interventions)
        print('population covered for interventions =', solution_population_coverage_interventions)
        print('budget unallocated =', total_budget-np.sum(solution_allocated_budget_patches) )
        optimization_model.print_information()
        print(optimization_model.solution)

        solution = {
            'allocated_budget_patches_interventions': solution_allocated_budget_patches_interventions,
            'allocated_budget_patches': solution_allocated_budget_patches,
            'coverage_patches_interventions': solution_coverage_patches_interventions,
            'allocated_budget_interventions': solution_allocated_budget_interventions,
            'population_coverage_interventions': solution_population_coverage_interventions,
            'population_coverage_patches_interventions': solution_population_coverage_patches_interventions,
            'R0': solution_r0,
            'base_r0': base_r0,
            'objectives': {
                'weighted_sum': weighted_sum,
                'max_r0': max_r0
            },
            'patch_ids': patch_ids,
            'intervention_names': config['intervention_names'],
            'population': population
        }

        return solution
