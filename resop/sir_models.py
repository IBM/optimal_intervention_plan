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

import numpy as np
import math


class BaseModel(object):
    def __init__(self, transmission, infectious_period):
        """
        Base model

        :param transmission: scalar, the transmission rate from those infectious to those susceptible
        :param infectious_period: scalar, the average infectious period
        """
        self.transmission = transmission
        self.infectious_period = infectious_period

    def run(self, previous_population, time_vector):
        raise NotImplementedError()

    def rnought(self):
        raise NotImplementedError()


class SIRModel(BaseModel):
    """
    Implementation of the basic 'SIR' (susceptible-infectious-removed) model for population number, with no demography
    or explicitly deaths due to the pathogen. Though arguably deaths due to pathogen could be considered to be included
    in the recovery rate (1/infectious_period in this implementation).
    """

    def __init__(self, transmission, infectious_period):
        """

        :param transmission: scalar, the transmission rate from those infectious to those susceptible
        :param infectious_period: scalar, the average infectious period
        """
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

    def parameters_string(self):
        return "(transmission infectious_period) = (%f %f)" % (self.transmission, self.infectious_period)

    def run(self, previous_population, time_vector):
        """
        call for ode solver, e.g. "populations = scint.odeint(sir_model_instance.run, initial_conditions, timespan)"
        :param previous_population: vector (S_0, I_0, R_0), with value for population at beginning of ODE solve time for
        each compartment
        :param time_vector: time vector [start day, assuming day increment, end day]
        :return: integrated population values
        """
        population = sum(previous_population)
        d_pop = np.zeros(3)

        # the set of differential equations to be solved
        d_pop[0] = -self.transmission * previous_population[0] * previous_population[1] / population
        d_pop[1] = self.transmission * previous_population[0] * previous_population[1] / population - previous_population[1] / self.infectious_period
        d_pop[2] = previous_population[1] / self.infectious_period

        return d_pop

    def rnought(self):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return self.transmission * self.infectious_period


class SEIRModel(BaseModel):
    """
    Implementation of a simple "SEIR" (suseptible-exposed-infectious-removed) for population number, with no demography.
    """

    def __init__(self, transmission, infectious_period, incubation_period):
        """

        :param transmission: scalar, the transmission rate from those infectious to those susceptible
        :param infectious_period: scalar, the average infectious period
        :param incubation_period: scalar, the average time between infection event and when able to infect others
        """
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

        self.incubation_period = incubation_period

    def parameters_string(self):
        return "(transmission incubation_period infectious_period) = (%f %f %f)" % (self.transmission, self.incubation_period, self.infectious_period)

    def run(self, previous_population, t):
        """
        call for ode solver, e.g. "populations = scint.odeint(sir_model_instance.run, initial_conditions, timespan)"
        :param previous_population: vector (S_0, E_0, I_0, R_0), with value for population at beginning of ODE solve time
        for each compartment
        :param t: time vector [start day, assuming day increment, end day]
        :return: the integrated population values
        """
        population = sum(previous_population)
        d_pop = np.zeros(4)

        # the set of differential equations to be solved
        d_pop[0] = -self.transmission * previous_population[0] * previous_population[2] / population
        d_pop[1] = self.transmission * previous_population[0] * previous_population[2] / population - previous_population[1] / self.incubation_period
        d_pop[2] = previous_population[1] / self.incubation_period - previous_population[2] / self.infectious_period
        d_pop[3] = previous_population[2] / self.infectious_period

        return d_pop

    def rnought(self):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return self.transmission * self.infectious_period


class SIRSModel(BaseModel):
    """
    Implementation of the basic 'SIRS' (susceptible-infectious-removed-susceptible) model for population number, with no
    demography. If waning_immunity==0, recover the SIR model.
    """

    def __init__(self, transmission, infectious_period, waning_immunity):
        """

        :param transmission: scalar, the transmission rate from those infectious to those susceptible
        :param infectious_period: scalar, the average infectious period
        :param waning_immunity:
        """
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

        self.waning_immunity = waning_immunity

    def parameters_string(self):
        return "(transmission, infectious_period, waning_immunity) = (%f, %f, %f)" % (self.transmission, self.infectious_period, self.waning_immunity)

    def run(self, previous_population, time_vector):
        """
        call for ode solver, e.g. "populations = scint.odeint(sir_model_instance.run, initial_conditions, timespan)"
        :param previous_population: vector (S_0, I_0, R_0, Cumulative number infected), with value for population at
        beginning of ODE solve time for each compartment, plus for tracking the cumulative number infected. Keep in mind
        that reinfections are possible in this model, so (cumulative number) may be > (population size)
        :param time_vector: time vector [start day, assuming day increment, end day]
        :return: integrated population values, including cumulative number of infections
        """
        population = sum(previous_population)
        d_pop = np.zeros(4)

        # the set of differential equations to be solved
        d_pop[0] = -self.transmission * previous_population[0] * previous_population[1] / population + self.waning_immunity * previous_population[2]
        d_pop[1] = self.transmission * previous_population[0] * previous_population[1] / population - previous_population[1] / self.infectious_period
        d_pop[2] = previous_population[1] / self.infectious_period - self.waning_immunity * previous_population[2]

        d_pop[3] = self.transmission * previous_population[0] * previous_population[1] / population  # cumulative infections

        return d_pop

    def rnought(self):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return self.transmission * self.infectious_period


class SINRModel(BaseModel):
    """
    Implementation of an SIR model with 'n' infectious compartments. This changes the distribution of times an
    individual spends in the infectious compartment from exponential to gamma, to fixed times for n->infty.
    """

    def __init__(self, transmission, infectious_period, n):
        """

        :param transmission: scalar, the transmission rate from those infectious to those susceptible
        :param infectious_period: scalar, the average infectious period
        :param n: scalar, number of infectious compartments
        """
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

        self.n = n

    def parameters_string(self):
        return "(transmission infectious_period) = (%f %f)" % (self.transmission, self.infectious_period)

    def run(self, previous_population, time_vector):
        """
        call for ode solver, e.g. "populations = scint.odeint(sir_model_instance.run, initial_conditions, timespan)"
        :param previous_population: vector (S_0, In_0, R_0), with value for population at beginning of ODE solve time for
        each compartment, with 'n' initial I_0 values.
        :param time_vector: vector [start day, assuming day increment, end day]
        :return: the integrated population values, with 'n' infectious compartments
        """
        population = sum(previous_population)
        total_infectious = sum(previous_population[1:-2])
        d_pop = np.zeros((2 + self.n))

        # the set of differential equations to be solved
        d_pop[0] = -self.transmission * previous_population[0] * total_infectious / population
        d_pop[1] = self.transmission * previous_population[0] * total_infectious / population - self.n * previous_population[1] / self.infectious_period
        for i in range(2, 2 + self.n):
            d_pop[i] = self.n * (previous_population[i - 1] - previous_population[i]) / self.infectious_period
        d_pop[-1] = self.n * previous_population[-2] / self.infectious_period

        return d_pop

    def rnought(self, exp_growth):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return exp_growth / (1 / self.infectious_period * (1 - math.pow(exp_growth * self.infectious_period / self.n + 1, -self.n)))


class SIRMigrationModel(BaseModel):
    """
    Implementation of an SIR migration model (single SIR model per patch, don't track locals vs travellers)
    """

    def __init__(self, transmission, infectious_period, travel, patches):
        """

        :param transmission: vector of size patches, transmission rate for each patch
        :param infectious_period: vector of size patches, infectious period for each patch
        :param travel: 2D matrix of size patches x patches [(rows "to"), (columns "from")]
        :param patches: scalar, number of patches
        """
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

        self.travel = travel
        self.patches = patches

    def parameters_string(self):
        return "(transmission infectious_period patches travel) = (%f %f %f %s)" % \
               (self.transmission, self.infectious_period, self.patches, str(self.travel))

    def run(self, previous_population, time_vector):
        """

        :param previous_population: (flattened) 2D matrix of size [number compartments, number of patches]
        :param time_vector: time vector [start day, assuming day increment, end day]
        :return: integrated population values, for each compartment in each patch (for each time increment)
        """
        previous_population = previous_population.reshape(self.patches, -1)

        d_pop = np.zeros((4, self.patches))
        patch_populations = previous_population.sum(axis=1)  # this is a problem. It now includes cumulative number infected in each patch...
        leaving = sum(self.travel)

        # linear algebra version
        # dPop[0,:] = -self.transmission * previous_population[0,:] * previous_population[1, :] / patch_populations - np.matrixmultiply(leaving, previous_population[0,:]) + previous_population[0,:]*self.travel

        # iterating over patches version
        for i in range(0, self.patches):
            d_pop[0, i] = -self.transmission[i] * previous_population[i, 0] * previous_population[i, 1] / patch_populations[i] - leaving[i] * previous_population[i, 0] + np.dot(self.travel[i, :], previous_population[:, 0])
            d_pop[1, i] = self.transmission[i] * previous_population[i, 0] * previous_population[i, 1] / \
                         patch_populations[i] - previous_population[i, 1] / self.infectious_period[i] - leaving[i] * \
                         previous_population[i, 1] + np.dot(self.travel[i, :], previous_population[:, 1])
            d_pop[2, i] = previous_population[i, 1] / self.infectious_period[i] - leaving[i] * previous_population[i, 2] + np.dot(self.travel[i, :], previous_population[:, 2])
            d_pop[3, i] = self.transmission[i] * previous_population[i, 0] * previous_population[i, 1] / patch_populations[i]  # cumulative number infected in that patch

            return d_pop.flatten()

    def rnought(self):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return np.nan  # placeholder


class GammaContactModel(BaseModel):
    def __init__(self, transmission, infectious_period, incubation_period, shape, birth=0.0, death=0.0):
        BaseModel.__init__(self, transmission=transmission, infectious_period=infectious_period)

        self.incubation_period = incubation_period
        self.shape = shape
        self.birth = birth
        self.death = death

    def parameters_string(self):
        return "(transmission incubation_period infectious_period shape birth death) = (%f %f %f %f %f %f)" % \
               (self.transmission, self.incubation_period, self.infectious_period, self.shape, self.birth, self.death)

    def run(self, previous_population, time_vector):
        population = sum(previous_population)
        d_pop = np.zeros(4)

        # ODEs
        d_pop[0] = self.birth * population - self.shape * np.log(1 + self.transmission * previous_population[2] / (self.shape * population)) * previous_population[0] - self.death * previous_population[0]
        d_pop[1] = self.shape * np.log(1 + self.transmission * previous_population[2] / (self.shape * population)) * previous_population[0] - (1 / self.incubation_period + self.death) * previous_population[1]
        d_pop[2] = previous_population[1] / self.incubation_period - (1 / self.infectious_period + self.death) * previous_population[2]
        d_pop[3] = previous_population[2] / self.infectious_period - self.death * previous_population[3]

        return d_pop

    def rnought(self):
        """
        Calculate the basic reproduction number for this model
        :return: $R_0$
        """

        return np.nan  # placeholder


if __name__ == "__main__":
    """
    Default is currently to only run the "SIR" model
    """
    import scipy
    import scipy.integrate as scint

    # set model parameters
    duration = 365.0
    tx = 1.0
    infPeriod = 3.0
    initial_conditions = (999999.0, 1.0, 0.0)

    timespan = np.arange(1, duration)  # assuming starting at day 1 and time steps of a day and duration in days
    sirmodel = SIRModel(transmission=tx, infectious_period=infPeriod)
    sirpops = scint.odeint(sirmodel.run, initial_conditions, timespan)

    print(sirpops)
    print(sirpops[363][2])


