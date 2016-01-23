#!/usr/bin/gnuplot

# graph of Room temperature

# ******************************************************* General settings *****
set terminal png font "Helvetica" 11 size 640,228
set datafile separator ';'
set datafile missing "NaN"   # Ignore missing values
set grid
tz_offset = utc_offset / 3600 # GNUplot only works with UTC. Need to compensate
                              # for timezone ourselves.

# ************************************************************* Statistics *****
# stats to be calculated here
fname = "/tmp/sql21c.csv"
stats fname using 2 name "W" nooutput

W_min = W_min + utc_offset - 946684800
W_max = W_max + utc_offset - 946684800

# ****************************************************************** Title *****
#set title "Test graph -".utc_offset."-"

# ***************************************************************** X-axis *****
set xlabel "Date/Time"       # X-axis label
set xdata time               # Define that data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%a %d"            # Display dayname of the week on the X axis
#set xtics rotate by 40 right
set xrange [ W_min : W_max ]

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
unset key

# ***************************************************************** Output *****
set object 1 rect from screen 0,0 to screen 1,1 behind
set object 1 rect fc rgb "#eeeeee" fillstyle solid 1.0 noborder
set object 2 rect from graph 0,0 to graph 1,1 behind
set object 2 rect fc rgb "#ffffff" fillstyle solid 1.0 noborder
set output "/tmp/plotc.png"

# ***** PLOT *****
plot "/tmp/sql21c.csv"  using ($2+utc_offset):3 title "Temperature [degC]"      with points pt 5 ps 0.2\
