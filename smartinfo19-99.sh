#! /bin/bash

rf="/tmp/ubundiagd/smartinfo"

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda="/dev/disk/by-id/wwn-0x7914297948508409858x"
sdb="/dev/disk/by-id/wwn-0x1138954418312597505x"
sdc="/dev/disk/by-id/wwn-0x4891478331354402817x"
sdd="/dev/disk/by-id/wwn-0x2556643098891800577x"
sde="/dev/disk/by-id/wwn-0x13230455334254301185x"
#sdf
#sdg

if [[ ! -d /tmp/ubundiagd ]]; then
  mkdir /tmp/ubundiagd
fi

function smart1999 {
  if [[ ! -e $rf"-"$2"-i.dat" ]]; then
    # this is static info, therefore only get it if it's not there.
    smartctl -i $1 |awk 'NR>4' >$rf"-"$2"-i.dat"
  fi
  smartctl -A $1 |awk 'NR>7' >$rf"-"$2"-A.dat"
  smartctl -H $1 |awk 'NR>4' >$rf"-"$2"-H.dat"
  smartctl -l selftest $1 |grep '\# 1' >$rf"-"$2"-l.dat"
  chmod 777 $rf-*
}

touch $rf".lock"
smart1999 $sda "sda"
smart1999 $sdb "sdb"
smart1999 $sdc "sdc"
smart1999 $sdd "sdd"
smart1999 $sde "sde"
rm $rf".lock"
