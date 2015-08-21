#! /bin/bash

# This script is executed periodically by a cronjob.
# It prevents the use op repeated `sudo smartctl...` commands by `libsmart.py`
# The resulting data is stored in `/tmp/ubundiagd/*.dat` files and subsequently
# read by the daemons 19 and 99 using `libsmart.py`.

rf="/tmp/ubundiagd/smartinfo"

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda="wwn-0x7914297948508409858x"
sdb="wwn-0x1138954418312597505x"
sdc="wwn-0x4891478331354402817x"
sdd="wwn-0x2556643098891800577x"
sde="wwn-0x13230455334254301185x"
#sdf=""
#sdg=""

function smart1999 {
  if [[ ! -e $rf"-"$1"-i.dat" ]]; then
    # this is static info, therefore only get it if it's not there.
    smartctl -i "/dev/disk/by-id/"$1 |awk 'NR>4' >$rf"-"$1"-i.dat"
  fi
  smartctl -A "/dev/disk/by-id/"$1 |awk 'NR>7' >$rf"-"$1"-A.dat"
  smartctl -H "/dev/disk/by-id/"$1 |grep 'test result' >$rf"-"$1"-H.dat"
  smartctl -l selftest "/dev/disk/by-id/"$1 |grep '\# 1' >$rf"-"$1"-l.dat"
  chmod 744 $rf-*
}

if [[ ! -d /tmp/ubundiagd ]]; then
  mkdir /tmp/ubundiagd
fi

touch $rf".lock"
smart1999 $sda
smart1999 $sdb
smart1999 $sdc
smart1999 $sdd
smart1999 $sde
rm $rf".lock"