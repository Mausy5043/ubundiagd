#! /bin/bash

# 00-scriptmanager.sh is run periodically by a private cronjob.
# * It synchronises the local copy of ubundiagd with the current github branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

CLNT=$(hostname)
ME=$(whoami)
branch=$(cat "$HOME"/.ubundiagd.branch)

pushd "$HOME"/ubundiagd

# Synchronise local copy with "$branch"

 git fetch origin
 # Check which code has changed
 # git diff --name-only
 # git log --graph --oneline --date-order --decorate --color --all

 DIFFlibd=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./libdaemon.py)
 DIFFlibs=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./libsmart2.py)
 DIFFd11=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon11.py)
 DIFFd12=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon12.py)
 DIFFd13=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon13.py)
 DIFFd14=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon14.py)
 DIFFd15=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon15.py)
 DIFFd19=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon19.py)
 DIFFd21=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon21.py)
 DIFFd98=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon98.py)
 DIFFd99=$(git --no-pager diff --name-only "$branch"..origin/"$branch" -- ./daemon99.py)

 git pull
 git fetch origin
 git checkout "$branch"
 git reset --hard origin/"$branch" && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 ./*

if [[ ! -d /tmp/ubundiagd ]]; then
  mkdir /tmp/ubundiagd
fi

######## Stop daemons ######

if [[ -n "$DIFFd11" ]]; then
  logger -t ubundiagd "Source daemon11 has changed."
  ./daemon11.py stop
fi
if [[ -n "$DIFFd12" ]]; then
  logger -t ubundiagd "Source daemon12 has changed."
  ./daemon12.py stop
fi
if [[ -n "$DIFFd13" ]]; then
  logger -t ubundiagd "Source daemon13 has changed."
  ./daemon13.py stop
fi
if [[ -n "$DIFFd14" ]]; then
  logger -t ubundiagd "Source daemon14 has changed."
  ./daemon14.py stop
fi
if [[ -n "$DIFFd15" ]]; then
  logger -t ubundiagd "Source daemon15 has changed."
  ./daemon15.py stop
fi
if [[ -n "$DIFFd19" ]]; then
  logger -t ubundiagd "Source daemon19 has changed."
  ./daemon19.py stop
fi
if [[ -n "$DIFFd21" ]]; then
  logger -t ubundiagd "Source daemon21 has changed."
  ./daemon21.py stop
fi
if [[ -n "$DIFFd99" ]]; then
  logger -t ubundiagd "Source daemon99 has changed."
  ./daemon99.py stop
fi
if [[ -n "$DIFFd98" ]]; then
  logger -t ubundiagd "Source daemon98 has changed."
  ./daemon98.py stop
fi

if [[ -n "$DIFFlibd" ]]; then
  logger -t ubundiagd "Source libdaemon has changed."
  # stop all daemons
  ./daemon11.py stop
  ./daemon12.py stop
  ./daemon13.py stop
  ./daemon14.py stop
  ./daemon15.py stop
  ./daemon19.py stop
  ./daemon21.py stop
  ./daemon98.py stop
  ./daemon99.py stop
  rm ./libdaemon.pyc
fi

if [[ -n "$DIFFlibs" ]]; then
  logger -t ubundiagd "Source libsmart has changed."
  ./daemon19.py stop
  ./daemon99.py stop
  rm libsmart2.pyc
fi

######## (Re-)start daemons ######

function destale {
  if [ -e /tmp/ubundiagd/$1.pid ]; then
    if ! kill -0 $(cat /tmp/ubundiagd/$1.pid)  > /dev/null 2>&1; then
      logger -t ubundiagd "Stale daemon$1 pid-file found."
      rm /tmp/ubundiagd/$1.pid
      ./daemon$1.py start
    fi
  else
    logger -t ubundiagd "Found daemon$1 not running."
    ./daemon$1.py start
  fi
}

destale 11
destale 12
destale 13
destale 14
destale 15
destale 19
destale 21
destale 98
destale 99

popd
