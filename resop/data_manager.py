from ibmdbpy import IdaDataBase, IdaDataFrame
from . import data_frames
from . import data_consts


NumberTypes = (int, int, float)


class DataManager:
    def __init__(self, db_connection_url):
        """

        :param connection_url:
        """
        self._db_connection_url = db_connection_url
        self._db = None

        # Required properties
        self._run_id = None
        self._country_code = None
        self._country_admin_level = None
        self._disease_name = None
        self._budget_amount = None
        self._num_pieces = 5

        # Optional properties
        self._intervention_budgets = {}

    def create_data(self, run_id, country_code, country_admin_level, disease_name, budget_amount, num_pieces=5, **kwargs):
        """

        :param run_id: Task run GUID, i.e. "5a1e058fb5ffdb317ad9c3a3"
        :param country_code: Country code, i.e. "TW"
        :param country_admin_level: Administration level, i.e. "2"
        :param disease_name: Disease name, i.e. "Dengue"
        :param budget_amount: Budget amount, i.e. 1000000
        :param num_pieces: Number of pieces, i.e. 5
        :param kwargs: Optional named arguments, such as:
            name: "intervention_budgets", type: object
        :return:
        """

        # TODO: Check if _db is already connected!
        self._db = None

        # Required properties
        if run_id is not None and isinstance(run_id, basestring):
            self._run_id = run_id
        else:
            raise ValueError('Invalid argument value for "run_id"')

        if country_code is not None and isinstance(country_code, basestring):
            self._country_code = country_code
        else:
            raise ValueError('Invalid argument value for "country_code"')

        if country_admin_level is not None and isinstance(country_admin_level, types.IntType):
            self._country_admin_level = country_admin_level
        else:
            raise ValueError('Invalid argument value for "country_admin_level"')

        if disease_name is not None and isinstance(disease_name, basestring):
            self._disease_name = disease_name
        else:
            raise ValueError('Invalid argument value for "disease_name"')

        if budget_amount is not None and isinstance(budget_amount, NumberTypes):
            self._budget_amount = budget_amount
        else:
            raise ValueError('Invalid argument value for "budget_amount"')

        if num_pieces is not None and isinstance(num_pieces, NumberTypes):
            self._num_pieces = num_pieces
        else:
            raise ValueError('Invalid argument value for "num_pieces"')

        # Optional properties
        self._intervention_budgets = kwargs.get('intervention_budgets', {})

        # connect to database
        self._db = IdaDataBase(dsn=self._db_connection_url, verbose=True)

        # # update database with relevant information about this run
        self.add_run()

        # get the data in dataframes
        data = data_frames.DataDataFrames(self._db, self._run_id)

        # grab data and configure it to an outgoing payload
        outgoing_payload = data.create_data_for_optimisation()

        # close connection
        self._db.close()

        return outgoing_payload

    def _open_db(self):
        """
        Opens the database
        if the database (self._db) is open, returns False, as this didn't do anything
        if self._db is not open, opens it and returns True (hopefully reminding the user to close the connection later)
        :return: True iff the database was closed and is now open
        """
        db_open = False
        try:
            self._db.current_schema
        except:
            db_open = True
            self._db = IdaDataBase(dsn=self._db_connection_url, verbose=False)
        return db_open

    def add_run(self):
        """
        checks for the existence of the current run_id in the database
        if it exists, throw a value error
        if it doesn't exist, adds the current run_id with its relevant data
        """
        db_open = self._open_db()

        # check for run_id already existing
        sql_count = 'SELECT COUNT (RUN_ID) FROM %s WHERE RUN_ID = \'%s\'' % (data_consts.TBL_RUNS, self._run_id)
        num_existing = self._db.ida_query(sql_count)

        if num_existing[0] > 0:
            self.delete_run_by_id(run_id=self._run_id)

        # add this run_id in to the runs table
        sql_add = '''
        INSERT INTO %s (RUN_ID, BUDGET, GEO_ID, DISEASE_ID, ADMIN_LEVEL, NUM_PIECES)
        VALUES (\'%s\', %f, \'%s\', \'%s\', %d, %d)''' % \
                  (data_consts.TBL_RUNS, self._run_id, self._budget_amount, self._country_code,
                   self._disease_name, self._country_admin_level, self._num_pieces)
        self._db.ida_query(sql_add)

        # now add any budget details
        # for budget in self._intervention_budgets:

        # if we opened the database, then lets close it as well
        if db_open:
            self._db.close()

    def add_results(self, run_id, results_payload):
        """
        TODO: Adds the results of a run to the database

        :param run_id
        :param results_payload:
        :return:
        """
        raise NotImplementedError

    def delete_run_by_id(self, run_id):
        """
        If the run_id is in the database, delete all references to it and return True
        If the run_id is not in the database, return false (as it does not exist)
        :param run_id: the ID to be deleted if it exists
        :return: True if the ID used to exist, False if it didn't
        """
        db_open = self._open_db()

        # check for run_id already existing
        sql_count = 'SELECT COUNT (RUN_ID) FROM %s WHERE RUN_ID = \'%s\'' % (data_consts.TBL_RUNS, run_id)
        num_existing = self._db.ida_query(sql_count)

        if num_existing[0] == 0:
            if db_open:
                self._db.close()
            return False

        # The run ID may appear in four tables - results_interventions, results, patch_budgets, and runs:
        # for table_name in [TBL_RESULTS_INTERVENTIONS, TBL_RESULTS, TBL_PATCH_BUDGETS, TBL_RUNS]:
        for table_name in [data_consts.TBL_RESULTS_INTERVENTIONS, data_consts.TBL_PATCH_BUDGETS, data_consts.TBL_RUNS]:
            sql_tail = 'FROM %s WHERE RUN_ID = \'%s\'' % (table_name, run_id)
            print('SELECT COUNT %s' % sql_tail)
            count = self._db.ida_query('SELECT COUNT %s' % sql_tail)
            if count[0] > 0:
                self._db.ida_query('DELETE %s' % sql_tail)

        # if we opened the database, then lets close it as well
        if db_open:
            self._db.close()
        return True
