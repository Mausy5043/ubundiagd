#!/usr/bin/gnuplot

# graph of Room temperature

# ******************************************************* General settings *****
set terminal png font "Helvetica" 11
set datafile separator ';'
set datafile missing "NaN"   # Ignore missing values
set grid
tz_offset = utc_offset / 3600 # GNUplot only works with UTC. Need to compensate
                              # for timezone ourselves.

# ************************************************************* Statistics *****
# stats to be calculated here
fname = "/tmp/sql21e.csv"
stats fname using 2 name "Y" nooutput

Y_min = Y_min + utc_offset - 946684800
Y_max = Y_max + utc_offset - 946684800

# ****************************************************************** Title *****
#set title "Test graph -".utc_offset."-"

# ***************************************************************** X-axis *****
set xlabel "Date/Time"       # X-axis label
set xdata time               # Define that data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%b"            # Display monthname on the X axis
set xtics rotate by 40 right
set xrange [ Y_min : Y_max ]

# ***************************************************************** Y-axis *****
set ylabel "Temperature [degC]" # Title for Y-axis
#set yrange [10:20]
set autoscale y

# **************************************************************** Y2-axis *****
#set y2label "Raw values [mV]" # Title for Y2-axis
#set autoscale y2
#set y2tics border         # place ticks on second Y2-axis

# ***************************************************************** Legend *****
# generate a legend which is placed underneath the plot
#set key outside bottom center box title "-=legend=-"

# ***************************************************************** Output *****
set output "/tmp/plote.png"

# ***** PLOT *****
plot "/tmp/sql21e.csv"  using ($2+utc_offset):3 title "Temperature [degC]"      with dots\
