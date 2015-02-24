# -*- coding: utf-8 -*-
__author__ = 'Bohdan Mushkevych'

from grazer.workers.abstract_cli_worker import AbstractCliWorker


# -- settings.py --
#grazer_aws_redshift_prefix='ext.',
#grazer_aws_redshift_suffix='',
#grazer_package_manager_credentials={'root@grazer-1.mycompany.com': ''},
#grazer_hatchery_command='/mnt/ops-tools/aws_provision.py',
#grazer_worker_ami='AMI-IMAGE-ID',
#grazer_worker_environment='production',
#grazer_worker_size='m1.small',
#grazer_scraper_profile='grazer-scraper-%s.mycompany.com',
#grazer_reducer_profile='grazer-reducer-%s.mycompany.com',
#grazer_scraper_ratio=5000,
#grazer_reducer_ratio=250000,
#grazer_scraper_limit=45,
#grazer_reducer_limit=3,
#grazer_run_threshold=250,

# -- settings_production.py --
#grazer_hatchery_command='/mnt/devops/hatchery.py',
#grazer_redshift_host='REDSHIFT_HOST.redshift.amazonaws.com',
#grazer_redshift_db='REDSHIFT_DB',
#grazer_redshift_user='REDSHIFT_USER',
#grazer_redshift_password='REDSHIFT_PASSWORD',
#grazer_redshift_port=5439,

# -- context.py --
#         TREE_GRAZER_DAILY: _timetable_context_entry(
#             tree_name=TREE_GRAZER_DAILY,
#             tree_classname='synergy.scheduler.tree.TwoLevelTree',
#             enclosed_processes=[PROCESS_GRAZER_HATCHERY],
#             dependent_on=[],
#             mx_name=_TOKEN_GRAZER_HATCHERY,
#             mx_page=MX_PAGE_GRAZER),

## -- constants.py --
# MX_PAGE_GRAZER = 'grazer_details'
# TREE_GRAZER_DAILY = 'tree_grazer_daily'

# -- mongodd_supervisor_schema.js --
#        'GrazerWebScraperDaily' : {'state' : 'state_on', 'pid' : null},

# -- mongodb_workers_schema.js --
#db.scheduler_managed_entry.insert({'process_name': 'GrazerWebScraperDaily', 'state' : 'state_off', 'trigger_time': 'every 3600', 'pipeline_name': 'simplified_discrete', 'process_type': 'type_managed'});


import psycopg2
import fabric
import fabric.operations
import boto.ec2

from opstools.settings import settings as ops_settings
from opstools.aws_provision import provision
from synergy.conf import settings
from synergy.system.performance_tracker import UowAwareTracker
from grazer.model.model_constants import *

TABLE_SOURCE_VIEW = 'source_view'

# parameter {0}: ext.tbl_scrape_state
# parameter {1}: ext.tbl_scrape_content
SQL_ADDRESS_FALSE_POSITIVES = ("UPDATE {0} "
                               "SET scrape_state = 'STATE_EMBRYO' "
                               "FROM {0} AS src, "
                               "     (  SELECT inner_src.package_name AS package, inner_src.platform AS platform  "
                               "        FROM {0} AS inner_src "
                               "            LEFT JOIN {1} AS inner_ref "
                               "                ON inner_ref.package = inner_src.package_name "
                               "                AND inner_ref.platform = inner_src.platform "
                               "        WHERE inner_ref.package IS NULL "
                               "            AND inner_ref.platform IS NULL "
                               "            AND inner_src.scrape_state = 'STATE_SUCCESS') AS ref "
                               "WHERE ref.package = src.package_name "
                               "    AND ref.platform = src.platform")

# parameter {0}: defines scrape_state table name. anticipated value: ext.tbl_scrape_state
SQL_NEW_PACKAGES_TO_PROCESS = ("SELECT COUNT(*) "
                               "FROM {0} "
                               "WHERE scrape_state = 'STATE_EMBRYO' ")

# parameter {0}: defines scrape_state table name. anticipated value: ext.tbl_scrape_state
SQL_PACKAGES_TO_REPROCESS = ("SELECT COUNT(*) "
                             "FROM {0} "
                             "WHERE scrape_state IN ('STATE_SUCCESS', 'STATE_RESCRAPE_FAILURE', 'STATE_FAILURE') "
                             "    AND last_updated < GETDATE() - INTERVAL '180 days' "
                             "OR scrape_state = 'STATE_FAILURE' "
                             "    AND scrape_http_code IN (403, 500, 503, 522, 999) ")

# parameter {0}: ext.tbl_scrape_state
# parameter {1}: source_view
SQL_POPULATE_NEW_APP = ("INSERT INTO {0} (package_name, platform) "
                        "SELECT src.apppackage AS package_name, "
                        "       src.platform AS platform "
                        "FROM {1} AS src "
                        "LEFT OUTER JOIN {0} AS aps "
                        "   ON src.apppackage = aps.package_name "
                        "WHERE aps.package_name IS NULL ")


def fully_qualified_table_name(table_name):
    # fully qualified table name
    fqtn = settings.settings['grazer_aws_redshift_prefix'] + table_name + settings.settings['grazer_aws_redshift_suffix']
    return fqtn


class GrazerHatchery(AbstractCliWorker):
    """Python process that spawns multiple Amazon Instances and updates unit_of_work"""

    def __init__(self, process_name):
        super(GrazerHatchery, self).__init__(process_name)
        self.is_alive = False
        self.return_code = -1
        self.instances = []

    def __del__(self):
        super(GrazerHatchery, self).__del__()

    # **************** Abstract Methods ************************
    def _init_performance_ticker(self, logger):
        self.performance_ticker = UowAwareTracker(logger)
        self.performance_ticker.start()

    # **************** Process Supervisor Methods ************************
    def _poll_process(self):
        return self.is_alive, self.return_code

    def start_remote_package_manager(self):
        for host_name in settings.settings['grazer_package_manager_credentials']:
            fabric.operations.env.warn_only = True
            fabric.operations.env.abort_on_prompts = True
            fabric.operations.env.use_ssh_config = True
            fabric.operations.env.host_string = host_name

            run_result = fabric.operations.run(
                '/mnt/grazer/deployment/.ve/bin/python /mnt/grazer/deployment/launch.py -r --app PackageManager',
                pty=False)

            if run_result.succeeded:
                self.return_code = 0

            self.logger.info('Grazer App Package Manager at %s started with result = %r'
                             % (host_name, self.return_code))

    def start_remote_reducer(self):
        for host_name in settings.settings['grazer_package_manager_credentials']:
            fabric.operations.env.warn_only = True
            fabric.operations.env.abort_on_prompts = True
            fabric.operations.env.use_ssh_config = True
            fabric.operations.env.host_string = host_name

            run_result = fabric.operations.run('/mnt/grazer/deployment/.ve/bin/python '
                                               '/mnt/grazer/deployment/launch.py -r --app WebReducer',
                                               pty=False)

            if run_result.succeeded:
                self.return_code = 0

            self.logger.info('Grazer Scrape Reducer at %s started with result = %r'
                             % (host_name, self.return_code))

    def puppet_cert_remove(self, scrapers, reducers):
        for host_name in settings.settings['puppet_master_credentials']:
            fabric.operations.env.warn_only = True
            fabric.operations.env.abort_on_prompts = True
            fabric.operations.env.use_ssh_config = True
            fabric.operations.env.host_string = host_name

            fabric.operations.run('/opt/cert_clean.sh 1 %s grazer scraper' % scrapers, pty=False)
            fabric.operations.run('/opt/cert_clean.sh 1 %s grazer reducer' % reducers, pty=False)

    def address_false_positives(self):
        """ it is possible that RedShift silently crashes during Merge/COPY execution
          Method addresses false positives by comparing nominal state_table with the actual data table """
        self.execute_query(SQL_ADDRESS_FALSE_POSITIVES.format(fully_qualified_table_name(TABLE_SCRAPE_STATE),
                                                              fully_qualified_table_name(TABLE_SCRAPE_CONTENT)),
                           'SQL False Positives',
                           perform_commit=True)

    def populate_new_apps(self):
        self.execute_query(SQL_POPULATE_NEW_APP.format(fully_qualified_table_name(TABLE_SCRAPE_STATE),
                                                       TABLE_SOURCE_VIEW),
                           'SQL Insert New Packages',
                           perform_commit=True)

    def get_app_count(self):
        total_count = 0
        result_set = self.execute_query(
            SQL_NEW_PACKAGES_TO_PROCESS.format(fully_qualified_table_name(TABLE_SCRAPE_STATE)),
            'SQL Packages to Process',
            results_expected=True)
        if result_set:
            total_count = result_set[0][0]
            self.logger.info('Number of new packages to process: %r' % result_set[0][0])

        result_set = self.execute_query(
            SQL_PACKAGES_TO_REPROCESS.format(fully_qualified_table_name(TABLE_SCRAPE_STATE)),
            'SQL Packages to Reprocess',
            results_expected=True)
        if result_set:
            total_count += result_set[0][0]
            self.logger.info('Number of new packages to RE-process: %r' % result_set[0][0])

        return total_count

    def _start_process(self, start_timeperiod, end_timeperiod, arguments):
        self.logger.info('start: %s {' % self.process_name)
        try:
            self.is_alive = True

            # recover from RedShift crashes if they were earlier
            self.address_false_positives()

            # push new packages to the ext.tbl_scrape_state
            self.populate_new_apps()

            # Get number of packages to be scraped
            new_app_count = self.get_app_count()
            if new_app_count <= settings.settings['grazer_run_threshold']:
                self.return_code = 0
                self.logger.info('Number of packages to (re)scrape is below threshold %d vs %d. Skipping this run.'
                                 % (new_app_count, settings.settings['grazer_run_threshold']))
                return

            num_scrapers = max(new_app_count // settings.settings['grazer_scraper_ratio'], 1)
            num_scrapers = min(num_scrapers, settings.settings['grazer_scraper_limit'])
            self.logger.info('Number of scrapers to start: %d' % num_scrapers)

            num_reducers = max(new_app_count // settings.settings['grazer_reducer_ratio'], 1)
            num_reducers = min(num_reducers, settings.settings['grazer_reducer_limit'])
            self.logger.info('Number of reducers to start: %d' % num_reducers)

            self.logger.info('Purging existing Grazer SSL Certificates from Puppet Master...')
            self.puppet_cert_remove(num_scrapers, num_reducers)

            self.logger.info('Starting App Package Manager at: %r ...'
                             % settings.settings['grazer_package_manager_credentials'].keys())
            self.start_remote_package_manager()

            nodes_to_provision = {settings.settings['grazer_scraper_profile']: num_scrapers}
            if num_reducers >= 2:
                nodes_to_provision[settings.settings['grazer_reducer_profile']] = num_reducers

            # Connect to AWS to provision instances
            conn = boto.ec2.connect_to_region(region_name=ops_settings['REGION'],
                                              aws_access_key_id=ops_settings['AWS_KEY_ID'],
                                              aws_secret_access_key=ops_settings['AWS_SECRET_KEY'])

            fabric.operations.env.warn_only = True
            for profile, headcount in nodes_to_provision.iteritems():
                grazer_size = settings.settings['grazer_worker_size']
                grazer_ami = settings.settings['grazer_worker_ami']
                security_groups = settings.settings['security_groups']
                ssh_key = settings.settings['aws_ssh_key']
                persist_storage = settings.settings['persist_storage']

                run_result = provision(conn, grazer_size, security_groups, headcount, grazer_ami, profile, ssh_key,
                                       persist_storage=persist_storage, ami=grazer_ami)
                self.instances.extend(run_result.instances)

            if settings.settings['grazer_reducer_profile'] not in nodes_to_provision:
                # start at least one reducer
                self.start_remote_reducer()

            self.return_code = 0 if self.instances else -1
            self.logger.info('Completed %s with result = %r' % (self.process_name, self.return_code))
        except Exception:
            self.logger.error('Exception on starting: %s' % self.process_name, exc_info=True)
            self.return_code = -1
        finally:
            self.logger.info('}')
            self.is_alive = False

    def execute_query(self, sql_query, sql_description, perform_commit=False, results_expected=False):
        result_set = []
        with psycopg2.connect(host=settings.settings['grazer_redshift_host'],
                              database=settings.settings['grazer_redshift_db'],
                              user=settings.settings['grazer_redshift_user'],
                              password=settings.settings['grazer_redshift_password'],
                              port=settings.settings['grazer_redshift_port']) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql_query)

                    if results_expected:
                        result_set = cursor.fetchall()
                    if perform_commit:
                        conn.commit()

                    self.logger.info('%s SUCCESSFUL. Status message: %s' % (sql_description, cursor.statusmessage))
                except Exception:
                    self.logger.error('%s FAILED. SQL = %s' % (sql_description, sql_query), exc_info=True)
        return result_set
