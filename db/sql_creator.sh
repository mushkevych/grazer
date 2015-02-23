#!/bin/bash

if [ $# -lt 1 ]; then
    echo ""
    echo "Description: script converts grazer schema template into a valid sql script file. "
    echo "Usage: `basename $0` schema_name"
    echo "Where: "
    echo "- schema name could be ext. "
    echo "Proceeding with defaults."
fi

prefix=${1:-'ext.'}

rm grazer_schema.sql
sed "s/%PREFIX%/${prefix}/g;s/%SUFFIX%//g" grazer_schema_template.sql > grazer_schema.sql
#sed "s/%PREFIX%/${prefix}/g;s/%SUFFIX%/_test/g" grazer_schema_template.sql >> grazer_schema.sql
