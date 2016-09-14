# MySQL script
# create table for winddata from NL Gilze-Rijen wetherstation

USE domotica;

DROP TABLE IF EXISTS wind;

CREATE TABLE `wind` (
  `sample_time`  datetime,
  `sample_epoch` int(11) unsigned,
  `speed`        decimal(6,3),
  `direction`    decimal(6,3),
  PRIMARY KEY (`sample_time`),
  INDEX (`sample_epoch`)
  ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;

# retrieve data:
-- mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM wind where (sample_time) >=NOW() - INTERVAL 6 HOUR;" | sed 's/\t/;/g;s/\n//g' > /tmp/sql.csv
