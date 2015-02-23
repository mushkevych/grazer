DROP TABLE %PREFIX%tbl_scrape_state%SUFFIX%;
CREATE TABLE %PREFIX%tbl_scrape_state%SUFFIX% (
  package_name VARCHAR(765) NOT NULL,
  platform VARCHAR(32) NOT NULL,                       -- android, apple, blackberry, etc
  store_url VARCHAR(256) DEFAULT NULL,                 -- store base URL
  scrape_state VARCHAR(24) DEFAULT 'STATE_EMBRYO',    -- enum: STATE_EMBRYO, STATE_SUCCESS, STATE_FAILURE, STATE_RESCRAPE_FAILURE
  scrape_url VARCHAR(256) DEFAULT NULL,                -- url we used to scrape package information
  scrape_http_code INTEGER DEFAULT NULL,               -- HTTP code of the scrape
  last_updated TIMESTAMP DEFAULT '20100101 00:01',
  PRIMARY KEY(package_name, platform)
)
sortkey(last_updated,tbl_scrape_state);

GRANT ALL PRIVILEGES
ON TABLE %PREFIX%tbl_scrape_state%SUFFIX%
TO ext;

DROP TABLE %PREFIX%temp_scrape_state%SUFFIX%;
CREATE TABLE %PREFIX%temp_scrape_state%SUFFIX% (
  package_name VARCHAR(765) NOT NULL,
  platform VARCHAR(32) NOT NULL,                       -- android, apple, blackberry, etc
  store_url VARCHAR(256) DEFAULT NULL,                 -- store base URL
  scrape_state VARCHAR(24) DEFAULT 'STATE_EMBRYO',    -- enum: STATE_EMBRYO, STATE_SUCCESS, STATE_FAILURE
  scrape_url VARCHAR(256) DEFAULT NULL,                -- url we used to scrape package information
  scrape_http_code INTEGER DEFAULT NULL,               -- HTTP code of the scrape
  last_updated TIMESTAMP DEFAULT '20100101 00:01',
  PRIMARY KEY(package_name, platform)
)
sortkey(last_updated,tbl_scrape_state);

GRANT ALL PRIVILEGES
ON TABLE %PREFIX%temp_scrape_state%SUFFIX%
TO ext;

DROP TABLE %PREFIX%temp_scrape_content%SUFFIX%;
CREATE TABLE %PREFIX%temp_scrape_content%SUFFIX% (
  -- tbl_scrape_state fields
  package_name VARCHAR(765) NOT NULL,
  platform VARCHAR(32) NOT NULL,
  store_url VARCHAR(256) DEFAULT NULL,                 -- store base URL
  scrape_state VARCHAR(24) DEFAULT 'STATE_EMBRYO',    -- enum: STATE_EMBRYO, STATE_SUCCESS, STATE_FAILURE
  scrape_url VARCHAR(256) DEFAULT NULL,                -- url we used to scrape package information
  scrape_http_code INTEGER DEFAULT NULL,               -- HTTP code of the scrape
  last_updated TIMESTAMP DEFAULT '20100101 00:01',

  -- scrape_content fields
  entry_id VARCHAR(128) NOT NULL,
  content_url VARCHAR(256) DEFAULT NULL,               -- application end url
  title VARCHAR(200) NOT NULL,
  category VARCHAR(128) NOT NULL,
  category_path VARCHAR(256) NOT NULL,
  release_date TIMESTAMP DEFAULT '20100101 00:01',
  version VARCHAR(32) NOT NULL,
  rating VARCHAR(32) NOT NULL,
  rating_count VARCHAR(32) NOT NULL,
  description VARCHAR(2048) NOT NULL,
  price VARCHAR(16) NOT NULL,
  developer VARCHAR(128) NOT NULL,
  seller VARCHAR(128) NOT NULL,
  cover_url VARCHAR(256) NOT NULL,
  PRIMARY KEY(package_name, platform)
)
sortkey(package_name,platform);

GRANT ALL PRIVILEGES
ON TABLE %PREFIX%temp_scrape_content%SUFFIX%
TO ext;


DROP TABLE %PREFIX%tbl_scrape_content%SUFFIX%;
CREATE TABLE %PREFIX%tbl_scrape_content%SUFFIX% (
  package VARCHAR(765) NOT NULL,
  platform VARCHAR(50) NOT NULL,
  title VARCHAR(200),
  primary_category VARCHAR(200),
  category_string VARCHAR(1000),
  description VARCHAR(20000),
  creator VARCHAR(200),
  seller VARCHAR(200),
  view_url VARCHAR(200),
  cover_art_url VARCHAR(200),
  version varchar(50),
  price varchar(50),
  rating varchar(32),
  rating_count varchar(32),
  release_date  TIMESTAMP ,
  updated_at TIMESTAMP,
  PRIMARY KEY(package, platform)
);

GRANT ALL PRIVILEGES
ON TABLE %PREFIX%tbl_scrape_content%SUFFIX%
TO ext;
