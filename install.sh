#! /bin/bash


sudo apt-get -yuV install mysql-client python-mysqldb
# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > /home/beheer/.ubundiagd.branch

exit 0
