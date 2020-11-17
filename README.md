# aur.resop

Optimization utilities for obtaining the optimized allocation of resources for a given objective.

`aur.resop` has been tested with Python `3.7.4`. 

## Installation

As a package:

```bash
$ python setup.py install
```

For development:

```bash
$ python setup.py develop
```

## Running an Optimization

This package uses CPLEX, either via DOCloud or locally installed CPLEX Studio.


### DOCloud

If using DOCloud you will need to supply the DOCloud API `url` and `key` as arguments to the script.

```bash
$ cd src/aur.resop/examples/
$ python intervention_plan_multi_patch.py --docloud_url "https://api-oaas.docloud.ibmcloud.com/job_manager/rest/v1" --docloud_client_id "<YOUR_API_KEY>"
```

### CPLEX Studio

You will need to ensure you have a license that enables running large optimizations! 

First install CPLEX Studio dependencies into your Python virtual environment:

```bash
$ python /Applications/CPLEX_Studio1210/python/setup.py install
```

Next, run the optimization as normal but without specifying the DOCloud API `url` and `key` arguments:

```bash
$ cd src/aur.resop/examples/
$ python intervention_plan_multi_patch.py 
```

## Optimization Results

If the script was successful you should see an output on the console similar to the following:

```bash
{'objectives': {'max': 1.84, 'weightedSum': 28270351.0}, 'interventions': [{'totalSpend': 565025.0, 'totalPopulationCoverage': 2354.0, 'intervention': u'Vaccinate'}, {'totalSpend': 1000000.0, 'totalPopulationCoverage': 11321880.0, 'intervention': u'Targetted larviciding'}, {'totalSpend': 34975.0, 'totalPopulationCoverage': 15812925.0, 'intervention': u'Vector control'}, {'totalSpend': 1000000.0, 'totalPopulationCoverage': 11168.0, 'intervention': u'Isolation'}], 'id': 'blah', 'patches': {'TW.TW.CL': {'details': [{'totalSpend': 0.0, 'populationCoverage': 0.0, 'coverage': 0.0, 'intervention': u'Vaccinate'}, {'totalSpend': 19216.0, 'populationCoverage': 216959.0, 'coverage': 0.7, 'intervention': u'Targetted larviciding'}, {'totalSpend': 480.0, 'populationCoverage': 216959.0, 'coverage': 0.7, 'intervention': u'Vector control'}, {'totalSpend': 0.0, 'populationCoverage': 0.0, 'coverage': 0.0, 'intervention': u'Isolation'}], 'id': 'TW.TW.CL', ...
``` 

## Changes

0.1
---
* Initial version.
# optimal_intervention_plan

## Contributors
  * Hamideh Anjomshoa
  * Stefan von Cavallar,
  * Olivia Smith,
  * Roslyn Hickson
  * Manoj Gambhier. 
