# ubundiagd
**Diagnostics Gatherer for Ubuntu Server**

This repository provides a number of python-based daemons that gather various system diagnostics. Although specifically targeted at my own Ubuntu Server (15.04), most will probably work (with minor modifications) on any Debian-based installation and probably also on other Linux systems.
The result of each deamon is a file containing comma-separated-values created in `/tmp/ubundiagd/`

The code used to daemonise python code was borrowed from previous work by:
- Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)
- Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)

and modified for my particular use-case. This includes a bash-script that keeps the daemons running. 

NO code is provided for further processing of the data. E.g. adding the data to a rrdtool-database and/or graphing the data. This functionality is offered elsewhere.

Following daemons are provided:
- daemon11 - CPU and motherboard temperature in degC (requires `lm-sensors`)
- daemon12 - CPU load (from `/proc/loadavg` and `vmstat`)
- daemon13 - Network interfaces (bytes in/out from `/proc/net/dev`)
- daemon14 - Memory usage (from `/proc/meminfo`)
- daemon15 - Size of logfiles (`kern.log`, `smartd.log` and `syslog.log`)
- daemon19 - Temperature of the disk-array in degC (requires `smartmontools`)
- daemon99 - Data uploading to the server
