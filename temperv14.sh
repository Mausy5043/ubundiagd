#! /bin/bash

of="/tmp/temperv14.dat"
lf="/tmp/temperv14.lock"

touch $lf
/srv/array1/rbin/boson/temperv14 -c >$of
chmod 777 $of
rm $lf
