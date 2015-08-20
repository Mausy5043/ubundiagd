#! /bin/bash

of="/tmp/ubundiagd/temperv14.dat"
lf="/tmp/ubundiagd/temperv14.lock"

if [[ ! -d /tmp/ubundiagd ]]; then
  mkdir /tmp/ubundiagd
fi

touch $lf
/srv/array1/rbin/boson/temperv14 -c >$of
chmod 777 $of
rm $lf
