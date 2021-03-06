#!/bin/bash

sleep 30

LOCAL=$(date)
LOCALSECONDS=$(date -d "$LOCAL" +%s)
UTC=$(date -u -d "$LOCAL" +"%Y-%m-%d %H:%M:%S")  #remove timezone reference
UTCSECONDS=$(date -d "$UTC" +%s)
UTCOFFSET=$(($LOCALSECONDS-$UTCSECONDS))

pushd $HOME/ubundiagd
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM temper where (sample_time) >=NOW() - INTERVAL 25 HOUR;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql21b.csv
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM temper where (sample_time) >=NOW() - INTERVAL 8 DAY;"   | sed 's/\t/;/g;s/\n//g' > /tmp/sql21c.csv
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM temper where (sample_time) >=NOW() - INTERVAL 32 DAY;"  | sed 's/\t/;/g;s/\n//g' > /tmp/sql21d.csv
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM temper where (sample_time) >=NOW() - INTERVAL 370 DAY;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql21e.csv
 # mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM wind where (sample_time) >=NOW() - INTERVAL 50 HOUR;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql29.csv

  touch /tmp/ubundiagd/graph.lock

  gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph21b.gp
  gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph21c.gp
  gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph21d.gp
  gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph21e.gp
  #gnuplot -e "utc_offset='${UTCOFFSET}'" ./graph29.gp
  #./graph29.py
  chown beheer:users /tmp/*.png
  mv /tmp/plot*.png  /var/www/status/
  mv /tmp/again*.png /var/www/weer/

  rm /tmp/ubundiagd/graph.lock
popd
