ENVIRONMENT = '%ENVIRONMENT%'

# folder locations, connection properties etc
settings = dict(
    process_prefix='Grazer',      # global prefix that is added to every process name started for synergy-data
    process_cwd='/mnt/tmp',     # daemonized process working directory, where it can create .cache and other folders

    mq_timeout_sec=300.0,
    mq_queue='default_queue',
    mq_routing_key='default_routing_key',
    mq_exchange='default_exchange',
    mq_durable=True,
    mq_exclusive=False,
    mq_auto_delete=False,
    mq_delivery_mode=2,
    mq_no_ack=False,

    aws_access_key_id='***AWS_KEY***',
    aws_secret_access_key='***AWS_SECRET_KEY***',
    aws_s3_bucket='grazer-scrapes',
    aws_redshift_grazer_prefix='ext.',
    aws_redshift_grazer_suffix='',

    aws_redshift_host='REDSHIFT_HOST.redshift.amazonaws.com',
    aws_redshift_db='DB_NAME',
    aws_redshift_user='DB_USER',
    aws_redshift_password='DB_PASSWORD',
    aws_redshift_port=5439,

    log_directory='/mnt/logs/grazer/',
    pid_directory='/mnt/logs/grazer/',
    merge_bulk_threshold=10,
    sql_bulk_threshold=1024,
    csv_bulk_threshold=16384,
    scrape_threads_count=5,

    perf_ticker_interval=60,    # seconds between performance ticker messages
    debug=False,                # if True - logger is given additional "console" adapter
    under_test=False,
)

amazon_appstore_urls = [
    'http://www.amazon.com/gp/mas/dl/android?p=%s',
]

https_proxy_list = ['']


# For now just two level... we can have configs for all deployments
# Need to have a better way for switching these
try:
    overrides = __import__('settings_' + ENVIRONMENT)
except:
    overrides = __import__('settings_dev')
settings.update(overrides.settings)


# Modules to test and verify (pylint/pep8)
testable_modules = [
    'model',
    'system',
    'workers',
]

test_cases = [
    'tests.test_scraper_engines',
    'tests.test_scrape_reducer',
]


def enable_test_mode():
    if settings['under_test']:
        # test mode is already enabled
        return

    test_settings = dict(
        mq_timeout_sec=10.0,
        aws_s3_bucket=settings['aws_s3_bucket'] + '_test',
        aws_redshift_grazer_suffix='_test',
        mq_vhost='/unit_test',
        csv_bulk_threshold=64,
        debug=True,
        under_test=True,
    )
    settings.update(test_settings)

    from tests.ut_context import register_processes
    register_processes()
