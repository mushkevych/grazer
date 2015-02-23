Grazer
==========

Grazer project is a linearly-scalable content scraper. It features:
- hatchery that dynamically spawns AWS instances based on "roles"
- scraper state management, allowing to limit amount of content being (re)scraped
- Rabbit MQ to manage the work queue and provide linear scalability
Grazer is best run and managed by Synergy Scheduler.

configuration
---------

Grazer configuration is environment-specific and organized in **settings_XXX.py** files.
Most prominent settings are:

- aws_access_key_id:
- aws_secret_access_key: 
- aws_s3_bucket: grazer_scrapes
- aws_redshift_grazer_prefix: ''
- aws_redshift_grazer_suffix: ''
- sql_bulk_threshold: size of the batch read from the db 
- csv_bulk_threshold: size of the temporary buffer before the flush to filesystem
- merge_bulk_threshold: number of request to accumulate before the flush on Merger side
- scrape_threads_count: number of simultaneous web scraper threads  

db
---------

Grazer relies on presence of following tables in the ext. schema:
    
- ext.tbl_scrape_conent: permanent table, managed by DBA
- ext.tbl_scrape_state: permanent table, managed by DBA
- ext.temp_scrape_state: temporary table, managed by Grazer codebase
- ext.temp_scrape_content: temporary table, managed by Grazer codebase

to setup Grazer EXT schema perform:

    $> ./db/sql_creator.sh  
    $> YOUR_SQL_SHELL ./db/grazer_schema.sql

unit test suite
---------

Grazer codebase comes with a comprehensive Unit Test suite.


license:
---------

Apache 2.0 License:
http://www.apache.org/licenses/LICENSE-2.0

metafile:
---------

    /launch.py            main executing file  
    /process_starter.py   utility to start worker in daemon mode  
    /settings.py          configuration management  
    /scripts/             folder contains shell scripts  
    /system/              folder contains useful system-level modules  
    /tests/               folder contains unit test  
    /vendors/             folder contains Python libraries required for the project and installed in Python Virtual Environment  
    /worker/              folder of actual project's code  
