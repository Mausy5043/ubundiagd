#! /bin/bash

# `ubunbian-ua-netinst` installs `ubunboot` and makes sure it is run at the
# very first boot.

# `ubunboot` then installs additional packages and modifies the system
# configuration accordingly. Among others `ubundiagd` may be installed
# using `git clone`. Followed by calling this `install.sh` script

# Installing `ubunboot` requires:
# 1. Add a cronjob in `/etc/cron.d/` periodically running `00-scriptmanager`
#    to keep the daemons up-to-date
# 2. Add various start-stop scripts to `/etc/init.d/` to start the daemons
#    automagically at re-boot.
# 3. start each of the daemons for the first time.

# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > ~/.ubundiagd.branch

exit 0
