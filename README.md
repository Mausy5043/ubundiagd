# ubundiagd
**Diagnostics Gatherer for Ubuntu Server**

# LEGACY
This repository is superseded by the [lnxdiagd](https://github.com/Mausy5043/lnxdiagd) repository

This repository provides a number of python-based daemons that gather various system diagnostics. Although specifically targeted at my own Ubuntu Server (15.04), most will probably work (with minor modifications) on any Debian-based installation and probably also on other Linux systems.
The result of each daemon is a file containing comma-separated-values created in `/tmp/ubundiagd/`

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
- daemon21 - Ambient temperature as supplied by the TEMPer USB device. (requires `temperv14`; source supplied with this repository)
- daemon97 - Push data to MySQL-server
- daemon98 - Upload data to the server
- daemon99 - XML-file creation

The file `config.ini` contains the settings for each daemon. The following settings are provided:
- reporttime:       Every <reporttime> seconds the daemon stores a result in the <resultfile>.
- cycles:           Measurement data (samples) are kept and averaged across <cycles> number of reports. This setting-name is a bit of a misnomer. It will be renamed at a later time.
- samplespercycle:  The number of samples per cycle.
- lockfile:         The name of the file used for locking the resultfile.
- resultfile:       The name of the file used by daemon97.
- rawfile:          The name of the CSV-file used by daemon98.
- sqlcmd:           The MySQL command used to add the data to the database.
