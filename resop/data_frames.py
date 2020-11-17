from . import data_consts


class DataDataFrames:
    def __init__(self, db, run_id):
        """
        create a data manager with a given database connection based on a given run id
        :param db: a connection to a database that contains the relevant data
        :param run_id: the run id for which to retrieve data
        """
        self._run_id = run_id

        my_string = "SELECT * FROM %s WHERE RUN_ID = '%s';" % (data_consts.TBL_RUNS, run_id)
        # self._run_row = db.ida_query("SELECT * FROM %s WHERE RUN_ID = '%s';" % (data_consts.runs_name, run_id))
        self._run_row = db.ida_query(my_string)

        self.validate_exactly_one_row(self._run_row, "Runs", run_id)

        self._geo = self._run_row.ix[0]["GEO_ID"]
        self._admin_level = self._run_row.ix[0]["ADMIN_LEVEL"]
        self._disease = self._run_row.ix[0]["DISEASE_ID"]
        self._budget = self._run_row.ix[0]["BUDGET"]
        self._num_pieces = self._run_row.ix[0]["NUM_PIECES"]

        self._patches = db.ida_query("SELECT * FROM %s WHERE GEO_ID = '%s' AND ADMIN_LEVEL = '%s';"
                                     % (data_consts.TBL_PATCHES, self._geo, self._admin_level))
        self._params = db.ida_query("SELECT * FROM %s WHERE DISEASE_ID = '%s';"
                                    % (data_consts.TBL_DISEASE_PARAMS, self._disease))
        self._interventions = db.ida_query("SELECT * FROM %s WHERE DISEASE_ID = '%s';"
                                           % (data_consts.TBL_INTERVENTIONS, self._disease))
        self._disease_patch_params = db.ida_query("SELECT * FROM %s WHERE GEO_ID = '%s';"
                                                  % (data_consts.TBL_DISEASE_PATCH_PARAMS, self._geo))
        self._patch_budgets = db.ida_query("SELECT * FROM %s WHERE RUN_ID = '%s';"
                                           % (data_consts.TBL_PATCH_BUDGETS, self._run_id))
        self._intervention_budgets = db.ida_query("SELECT * FROM %s WHERE RUN_ID = '%s';"
                                                  % (data_consts.TBL_INTERVENTION_BUDGETS, self._run_id))
        self._intervention_cost_breaks = db.ida_query("SELECT * FROM %s WHERE GEO_ID = '%s';"
                                                      % (data_consts.TBL_INTERVENTION_COST_BREAKPOINTS, self._geo))
        self._intervention_patch_params = db.ida_query("SELECT * FROM %s WHERE GEO_ID = '%s';"
                                                       % (data_consts.TBL_INTERVENTION_PATCH_PARAMS, self._geo))
        self._params_list = db.ida_query("SELECT DISTINCT PARAMETER_ID FROM %s WHERE DISEASE_ID = '%s';"
                                         % (data_consts.TBL_DISEASE_PARAMS, self._disease)).tolist()
        self._breakpoint_list = db.ida_query("SELECT DISTINCT COVERAGE_VAL FROM %s WHERE GEO_ID = '%s';"
                                             % (data_consts.TBL_INTERVENTION_COST_BREAKPOINTS, self._geo)).tolist()
        self._interventions_list = db.ida_query("SELECT DISTINCT INTERVENTION_ID FROM %s WHERE DISEASE_ID = '%s';"
                                                % (data_consts.TBL_INTERVENTIONS, self._disease)).tolist()

    def create_data_for_optimisation(self):
        """
        create the data required for optimisation
        :return: formatted data
        """
        patches = {}
        config = self.make_config_entry()
        print(self._patches)
        for name in self._patches["PATCH_ID"]:
            patches[name] = self.make_patch_dictionary_from_id(name)
        return{"patches": patches,
               "config": config}

    def make_config_entry(self):
        """
        create the config dictionary for input in to the optimisation model.
        :return: a config dictionary
        """
        interventions = self._interventions["INTERVENTION_ID"].tolist()
        min_budget = [0] * len(interventions)
        max_budget = [self._budget.value] * len(interventions)
        for index, row in self._intervention_budgets.iterrows():
            ix = interventions.index(row["INTERVENTION_ID"])
            if row["UPPER_BOUND"] is not None:
                max_budget[ix] = row["UPPER_BOUND"].value
            if row["LOWER_BOUND"] is not None:
                min_budget[ix] = row["LOWER_BOUND"].value
        config = {
            "num_interventions": self._interventions.shape[0],
            "num_pieces": self._num_pieces.item(),
            "intervention_names": interventions,
            "total_budget": self._budget.value,
            "minimum_intervention_budget": min_budget,
            "maximum_intervention_budget": max_budget
        }
        return config

    def make_patch_dictionary_from_id(self, patch_id):
        """
        returns a patch dictionary from its id.  A patch is structured as follows:
        {
            "name": patch_name,
            "population": patch_row.iloc[0]["POPULATION"].item(),
            "minimum_patch_budget": min_patch_budget
            "XXX": the base value for parameter XXX in this patch.  This exists for each parameter XXX
            "threshold_coverage":  an double indexed array - for each intervention,
                    an array of all breakpoints for coverage
            "threshold costs: a double indexed array - for each intervention,
                    an array of the cost of coverage at each breakpoint.
            "efficacy XXX": an array - for each intervention, its efficacies for this patch.
                    This exists for each parameter XXX
        }
        :param patch_id:
        :return: a patch dictionary as described above
        """
        # start by setting up the shorter parameters
        # get the appropriate row from the database
        patch_row = self._patches[self._patches["PATCH_ID"] == patch_id]
        self.validate_exactly_one_row(patch_row, "patches", patch_id)
        # find budget data for the right patch and run
        first_one = self._patch_budgets["PATCH_ID"] == patch_id
        second_one = self._patch_budgets["RUN_ID"] == self._run_id
        bools = first_one & second_one
        patch_budget_row = self._patch_budgets[bools]
        # find the minimum patch budget for this patch
        if patch_budget_row.shape[0] == 0:
            min_patch_budget = 0
        else:
            self.validate_exactly_one_row(patch_budget_row, "patch_budget", "%s %s" % (patch_id, self._run_id))
            min_patch_budget = patch_budget_row.iloc[0]["LOWER_BOUND"]
            if min_patch_budget is None:
                min_patch_budget = 0

        # start by setting the simple parameters in patch for returning
        patch = {"name": patch_id,
                 "population": patch_row.iloc[0]["POPULATION"].item(),
                 "minimum_patch_budget": min_patch_budget
                 }

        # now working on the indexed parts of the patch dictionary
        params = self._disease_patch_params
        efficacy_params = self._intervention_patch_params

        # grab out the values (x coordinates) of the breakpoints and copy them for each intervention
        my_breakpoints = map(lambda x: x.value, self._breakpoint_list)
        my_breakpoints = [my_breakpoints for _ in self._interventions_list]
        patch["threshold_coverage"] = my_breakpoints

        # starting to build up threshold cost information
        threshold_costs = [[0] * len(self._breakpoint_list) for _ in self._interventions_list]

        # data that's needed for each parameter comes from this loop
        for param in self._params_list:
            name_string = "efficacy" + param
            efficacies = [0 for _ in self._interventions_list]
            thresholds = self._intervention_cost_breaks
            self._breakpoint_list.sort()

            for intervention in self._interventions_list:
                # grab the appropriate data for a given intervention efficacies
                intervention_ix = self._interventions_list.index(intervention)
                ix = self._interventions_list.index(intervention)
                efficacies_row = efficacy_params[((efficacy_params["PATCH_ID"] == patch_id) &
                                                  (efficacy_params["PARAMETER_ID"] == param) &
                                                  (efficacy_params["GEO_ID"] == self._geo) &
                                                  (efficacy_params["INTERVENTION_ID"] == intervention))]
                self.validate_exactly_one_row(efficacies_row, "patch parameters", patch_id + " " + param + " " + self._geo)
                efficacies[ix] = efficacies_row.iloc[0]["IMPACT"].value

                for threshold in self._breakpoint_list:
                    # grab the data for the cost of the intervention at each breakpoint
                    ix = self._breakpoint_list.index(threshold)
                    thresholds_row = thresholds[((thresholds["PATCH_ID"] == patch_id) &
                                                 (thresholds["GEO_ID"] == self._geo) &
                                                 (thresholds["INTERVENTION_ID"] == intervention) &
                                                 (thresholds["COVERAGE_VAL"] == threshold))]
                    self.validate_exactly_one_row(thresholds_row, "cost breakpoints", "%s %s %s %s"
                                                  % (patch_id, self._geo, intervention, threshold))
                    threshold_costs[intervention_ix][ix] = thresholds_row.iloc[0]["COST"].value

            # set efficacy data for this intervention
            patch[name_string] = efficacies

            # get data for this disease parameter for this patch
            params_df = self._disease_patch_params
            param_row = params_df[(params_df["PATCH_ID"] == patch_id) & (params["PARAMETER_ID"] == param) &
                                  (params_df["GEO_ID"] == self._geo)]
            self.validate_exactly_one_row(param_row, "disease patch params", "%s %s %s" % (patch_id, param, self._geo))

            # and add it to the patch summary
            patch[param] = param_row.iloc[0]["VALUE"].value

        # add in costs
        patch["threshold_costs"] = threshold_costs
        return patch

    def validate_exactly_one_row(self, table, table_name, id_val):
        """
        check that table has exactly one row.  Raises an error if not.
        :param table: the table that should contain one row
        :param table_name: the name of the table for reporting an error if required
        :param id_val: the id that should have found one row for reporting an error if required
        """
        if table.shape[0] == 0:
            raise ValueError("The database does not have an entry in table %s for id %s."
                             % (table_name, id_val))
        if table.shape[0] != 1:
            raise ValueError("The database somehow has the wrong number of entries in table %s for run id %s, %d"
                             % (table_name, id_val, table.shape[0]))

