#!/bin/bash

LOCAL=$(date)
LOCALSECONDS=$(date -d "$LOCAL" +%s)
UTC=$(date -u -d "$LOCAL" +"%Y-%m-%d %H:%M:%S")  #remove timezone reference
UTCSECONDS=$(date -d "$UTC" +%s)
UTCOFFSET=$(($LOCALSECONDS-$UTCSECONDS))

pushd $HOME/ubundiagd
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM tmp36 where (sample_time) >=NOW() - INTERVAL 7 DAY;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql21.csv
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM temper where (sample_time) >=NOW() - INTERVAL 7 DAY;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql21b.csv
  gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph21.gp
popd
