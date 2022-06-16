#!/usr/bin/bash

# Update the predicted cooldown temperature.
# === Perhaps this will be better done by a cron job.
# So that this CGI script does not have to generate
# any temporary files.

exec 2> /tmp/graphss.err


RRD_DIR=/gpc/conf/rrd
GRAPH_WIDTH=528
GRAPH_HEIGHT=336
RRDTOOL=/gpc/bin/rrdtool
RRDGRAPH="$RRDTOOL graph -E -T 110 --units=si"
RRDFETCH="$RRDTOOL fetch"
SSGET=/gpc/bin/ssGet
SSGETCMT=/gpc/bin/ssGetCmt

# Pick up settings from control system config.
. ../../common.sh

# Last control loop state.
control_state=$($SSGET "$SS_CONTROL_STATE")

# Times where we're allowed to run.
day_begin=$($SSGET "$SS_DAY_BEGIN")
day_end=$($SSGET "$SS_DAY_END")

# Name of the script determines which camera we're on.
case "$(basename $0)" in
  graphss_h2rg.cgi)
    CAM=h2rg
    CAMNAME="H2RG Cam 1"  
    ;;
  graphss_h2rg2.cgi)
    CAM=h2rg2
    CAMNAME="H2RG Cam 2"  
    ;;
esac

# Camera-specific colours.
case "$CAM" in

  # DL cam 1 is based on a green colour scheme.
  h2rg)
    COLOR_PANEL="DarkGreen"
    COLOR_BG="DarkGreen"
    COLOR_FG="LightGrey"
    COLOR_LINK="LightGreen"
    ;;
    
  # DL cam 2 is based on a dark blue scheme.
  h2rg2)
    COLOR_PANEL="DarkBlue"
    COLOR_BG="MidnightBlue"
    COLOR_FG="LightGrey"
    COLOR_LINK="LightBlue"
    ;;

  *) # Default to lab-style colours.
    COLOR_PANEL="#e8c870"
    COLOR_BG="#503010"
    ;;
esac

color0="#dd1111"
color1="#ccb050"
color2="#f0a000"
color3="#00b000"
color4="#5030ff"
color5="#a0c0ff"
color6="#ff60ff"
color7="#999999"
color8="#661111"
color9="#7f0000"

# Dimmer versions of the same colours. Handy tool at
# http://www.drpeterjones.com/colorcalc/ for generating
# dimmer colours.
color_mid0="#aa0d0d"
color_mid1="#99843c"
color_mid2="#Bd7e00"
color_mid3="#007D00"
color_mid4="#4026CC"
color_mid5="#809ACC"
color_mid6="#CC4DCC"
color_mid7="#666666"
color_mid8="#330909"
color_mid9="#4C0000"

color_dim0="#770909"
color_dim1="#665828"
color_dim2="#8a5c00"
color_dim3="#004A00"
color_dim4="#301D99"
color_dim5="#607399"
color_dim6="#993A99"
color_dim7="#333333"
color_dim8="#201010"
color_dim9="#190000"

GRAPHOPTS="-h $GRAPH_HEIGHT -w $GRAPH_WIDTH \
--font AXIS:5:/usr/wm/common/fonts/TrueType/tahoma.ttf \
--font DEFAULT:10:/usr/wm/common/fonts/TrueType/tahoma.ttf \
--font LEGEND:9 \
--font TITLE:13:/usr/wm/common/fonts/TrueType/tahomabd.ttf \
--font WATERMARK:7 \
--tabwidth 30"

THUMBOPTS="-h 76 -w 76 -j"

###############################################################################
# HEATER CONTROL GRAPHS

# Main display of system temperatures.
generate_water_heater_temps ()
{
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_temps_lt"
  RRD_FILE_HOUSE="$RRD_DIR/water_tank_supply_lt"
  
  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_generate_water_heater_temps"
  fi

  # Info from the database. We care about the three temperatures,
  # and the state of the pump.
  set - "$@" "DEF:temp_tank=$RRD_FILE:temp_tank:MAX"
  set - "$@" "DEF:temp_return=$RRD_FILE:temp_return:MAX"
  set - "$@" "DEF:temp_pump=$RRD_FILE:temp_pump:MAX"
  set - "$@" "DEF:pump_state=$RRD_FILE:pump_state:MAX"

  # The supply to the house (hot water out fitting) was an afterthought,
  # and is held in a separate database.
  set - "$@" "DEF:temp_supply=$RRD_FILE_HOUSE:temp_supply:MAX"

  # Because 'murca, temps are often expressed in F.
  set - "$@" "CDEF:temp_tank_f=temp_tank,1.8,*,32,+"

  # Delta between temperatures.
  set - "$@" "CDEF:temp_delta=temp_return,temp_tank,-"

  # Produce a visual indication of the periods when the pump
  # is off. These will be an area behind the temperature traces.
  set - "$@" "CDEF:pump_background=pump_state,0,EQ,INF,UNKN,IF"
  #set - "$@" "CDEF:pump_off_area=1,pump_state,-,60*"

  # Pump state goes behind the temperatures.
  set - "$@" "AREA:pump_background#EAEAEA"

  # Plot Temperatures for the parts of the system we care about.
  set - "$@" "LINE3:temp_tank${color0}: tank\g"
  set - "$@" "GPRINT:temp_tank:LAST: (%4.1lfC"
  set - "$@" "GPRINT:temp_tank_f:LAST: %4.1lfF)\t"
  set - "$@" "LINE3:temp_return${color1}: return\g"
  set - "$@" "GPRINT:temp_return:LAST: (%4.1lfC)\t"
  set - "$@" "GPRINT:temp_delta:LAST: delta %4.1lfC \n"
  set - "$@" "LINE3:temp_supply${color7}: supply\g"
  set - "$@" "GPRINT:temp_supply:LAST: (%4.1lfC)\n"

  # Do we care about the temperature at the pump fitting?
  # Doesn't seem to change much with tank temperature.
  #set - "$@" "LINE3:temp_pump${color5}: pump\g"
  #set - "$@" "GPRINT:temp_pump:LAST:(%.1lfC)\n"

  # Probably doesn't need a pump state in the legend.
  # set - "$@" "GPRINT:pump_state:LAST:Pump %.0lf\n"
  
  # We don't really want to exceed this tank temperature.
  set - "$@" "HRULE:${MAX_TANK_TEMP}#cc5555"
  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -A --upper-limit 60 --lower-limit 28 --rigid - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}

# Autoscaled water tank temperature only.
generate_water_tank_temp ()
{
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_temps_lt"
  RRD_FILE_HOUSE="$RRD_DIR/water_tank_supply_lt"

  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_generate_water_tank_temp"
  fi

  # Info from the database. We care about the tank temperature
  # and the state of the pump.
  set - "$@" "DEF:temp_tank=$RRD_FILE:temp_tank:MAX"
  set - "$@" "DEF:pump_state=$RRD_FILE:pump_state:MAX"

  # Because 'murca, temps are often expressed in F.
  set - "$@" "CDEF:temp_tank_f=temp_tank,1.8,*,32,+"

  # Produce a visual indication of the periods when the pump
  # is off. These will be an area behind the temperature traces.
  set - "$@" "CDEF:pump_background=pump_state,0,EQ,INF,UNKN,IF"

  # Pump state goes behind the temperatures.
  set - "$@" "AREA:pump_background#EAEAEA"

  # Plot Temperatures for the parts of the system we care about.
  set - "$@" "LINE3:temp_tank${color0}: tank\g"
  set - "$@" "GPRINT:temp_tank:LAST: (%4.1lfC"
  set - "$@" "GPRINT:temp_tank_f:LAST: %4.1lfF)\n"

  # We don't really want to exceed this tank temperature.
  set - "$@" "HRULE:${MAX_TANK_TEMP}#cc5555"

  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -A --left-axis-format "%.1lf" - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}

# Autoscaled view of difference between the return and tank temperatures.
generate_water_heater_temp_delta ()
{
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_temps_lt"
  
  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_generate_water_heater_temp_delta"
  fi

  # Info from the database. We care about the tank and return
  # temperatures.
  set - "$@" "DEF:temp_tank=$RRD_FILE:temp_tank:MAX"
  set - "$@" "DEF:temp_return=$RRD_FILE:temp_return:MAX"

  # Delta between temperatures.
  set - "$@" "CDEF:temp_delta=temp_return,temp_tank,-"
  # Plot Temperatures for the parts of the system we care about.
  set - "$@" "LINE3:temp_delta${color3}: Temp delta\g"
  set - "$@" "GPRINT:temp_delta:LAST: (%4.1lfC)\n"

  # rrdgraph doesn't show the y origin on the plot. Make it a
  # little more obvious - this is a delta that will usually be above
  # while operating and below when the pump is off.
  set - "$@" "HRULE:0#a0a0a0"
  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -A --lower-limit -0.4 --upper-limit 4 - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}


###############################################################################
# HOST_GRAPHS
generate_host_temps () {
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_host_lt"
  
  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_host_temps"
  fi

  # Add definition for micropirani pressure.
  #
  set - "$@" "DEF:cpu_temp=$RRD_FILE:cpu_temp:MAX"

  # Draw a line and label it.
  #
  set - "$@" "LINE2:cpu_temp$color0: CPU"
  set - "$@" "GPRINT:cpu_temp:LAST: (%.1lf C)\n"
  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -M --lower-limit 0 - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}

generate_host_mem () {
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_host_lt"
  
  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_host_mem"
  fi

  # Add definition for micropirani pressure.
  #
  set - "$@" "DEF:mem_avail=$RRD_FILE:mem_avail:MAX"
  set - "$@" "DEF:mem_free=$RRD_FILE:mem_free:MAX"

  # RRD values are in kiB. Stick to MiB to make things simpler.
  set - "$@" "CDEF:mem_avail_mb=mem_avail,1024,/"
  set - "$@" "CDEF:mem_free_mb=mem_free,1024,/"
  
  # Draw a line and label it.
  #
  set - "$@" "LINE2:mem_avail_mb$color2: Avail"
  set - "$@" "GPRINT:mem_avail_mb:LAST: (%.1lf MiB)\t"
  set - "$@" "LINE2:mem_free_mb$color4: Free"
  set - "$@" "GPRINT:mem_free_mb:LAST: (%.1lf MiB)\n"
  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -M --lower-limit 0 - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}

###############################################################################
# GENERAL FUNCTIONS

generate_graph () {
  graph="$1"

  if [ -z "$graph" ] ; then
    return
    echo "No graph"
  elif [ "$graph" == "none" ] ; then
    echo "<P>No graph selected"
  else

    # Note use of inline-block for div style - this shrinks the div to the same size as the image it contains, rather
    # than letting it expand to fill the table cell.
    echo "<DIV style=\"display:inline-block\" ID=\"clickme$1\" onClick=\"click_to_centre(document, event, '$start', '$end', document['t\
heform'], '$graph')\"><IMG BORDER=0 SRC=\"$SCRIPT_NAME?$QUERY_STRING&png=$graph\"></DIV>"

    if [ "$graph" == "lab_nitrogen" ] ; then
      echo "<IMG SRC=\"https://svn.ifa.hawaii.edu/gpc/archive/n2flow/n2flow_pretty.jpeg\">"
    fi
  fi
}

ALL_GRAPHS="water_heater_temps \
water_tank_temp \
water_heater_temp_delta \
host_mem \
host_temps
"
GRAPH_TITLE_water_heater_temps="Water heater temperatures"
GRAPH_TITLE_water_tank_temp="&nbsp;&nbsp;&nbsp;Water tank temperature (autoscaled)"
GRAPH_TITLE_water_heater_temp_delta="Water heater temperature delta (return - tank)"
GRAPH_TITLE_host_mem="RPi mem info"
GRAPH_TITLE_host_temps="RPi host temps"

generate_pulldown () {
  graph="$1"
  eval option_selected=\$$graph

  
  echo "<SELECT NAME=\"$graph\" STYLE=\"font-size: 14pt\" onChange=\"submit()\">"
  
  for option in $ALL_GRAPHS none
  do
    eval title="\$GRAPH_TITLE_$option"
    selected=""
    if [ "$option_selected" == "$option" ] ; then
       selected="SELECTED" 
    fi
cat<<EOF
    <OPTION $selected VALUE="$option">$title</OPTION>
EOF

  done

  echo "</SELECT>"
}


set_defaults () {
  start="1 day ago"
  end="now"

  # Start with these graphs if they're not explicitly given.
  [ "$graph1" ] || graph1=water_heater_temps
  [ "$graph2" ] || graph2=water_heater_temp_delta
}

zoom_ago ()
{
  local op="$1"
  local n="$2"
  local units="$3"
  local ago="$4"

  shift

  local original_time="$@"

  # If the time given isn't a duration, then don't zoom.
  if [ "$ago" != "ago" ] ; then
    shift
    echo "$original_time"
    return
  fi

  case "$op" in
    out) n=$((n*2)) ;;
    in)
      # Zooming in can be a little problematic. If we're at an odd number
      # of units (or 1) then we can't divide that in half. Drop to the next
      # set of units and bump the duration accordingly.
      if [ $((n % 2)) -eq 1 ] ; then
        case "$units" in

	  month|month)
	    n=$((n*30))
	    units=day
	    ;;

	  week|week)
	    n=$((n*7))
	    units=day
	    ;;

	  day|days)
	    n=$((n*24))
	    units=hour
	    ;;

	  hour|hours)
	    n=$((n*60))
	    units=min
	    ;;

	  min|mins)
	    n=$((n*60))
	    units=sec
	    ;;

	  *) # At sec, we can't divide any further. Don't try.
            echo "$original_time"
	    return
	    ;;

	esac
      fi

      n=$((n/2))
      ;;
  esac
  echo "$n $units ago"
}

###############################################################################

set_defaults

savedIFS=$IFS
IFS='&'
set -- `echo "$QUERY_STRING" | sed -e 's/%3[aA]/:/g' -e 's/%..//g'`
IFS=$savedIFS
 
for arg; do
  opt="${arg#*=}"
  case "$arg" in
    graph1=*) graph1="$opt" ;;
    graph2=*) graph2="$opt" ;;
    graph3=*) graph3="$opt" ;;
    graph4=*) graph4="$opt" ;;
    png=*) png="$opt" ;;
    dat=*) dat="$opt" ;;
    start=*) start="$opt" ;;
    end=*) end="$opt" ;;
    zoomin=*) zoomin=yes ;;
    zoomout=*) zoomout=yes ;;
    panleft=*) panleft=yes ;;
    panright=*) panright=yes ;;
    follow=*) follow=yes ;;
    stopfollow=*) stopfollow=yes ;;
    reset=*) reset=yes ;;
  esac
done

# Here's a hack to look at old data, saved off in rrd.SAVE3:
#case "$dat" in
#  pkgtemp) RRD_DIR=/gpc/conf/rrd.SAVE3 ;;
#esac
#case "$png" in
#  pkgtemp) RRD_DIR=/gpc/conf/rrd.SAVE3 ;;
#esac

if [ "$reset" ]; then
  set_defaults
fi

if [ "$follow" ]; then
  end=now
fi

start=`echo $start | sed -e 's/+/ /g'`
end=`echo $end | sed -e 's/+/ /g'`

case "$start" in
  *[a-zA-Z]*) start_sec=`date +%s --date="$start"` ;;
  *) start_sec="$start" ;;
esac

case "$end" in
  *[a-zA-Z]*) end_sec=`date +%s --date="$end"` ;;
  *) end_sec="$end" ;;
esac

dur_sec=$(( end_sec - start_sec ))

if [ "$zoomout" ]; then
  if [ "$end" = "now" ]; then

    # If the graph starts a given period ago rather than
    # at a fixed point, then try and modify that.
    case "$start" in
      *ago) start=`zoom_ago out $start` ;;
      *)
        start_sec=$(( start_sec - dur_sec / 2 ))
        start=$start_sec
	;;
    esac
  else
    start_sec=$(( start_sec - dur_sec / 4 ))
    start=$start_sec
    end_sec=$(( end_sec + dur_sec / 4 ))
    end=$end_sec
  fi
fi

if [ "$zoomin" ]; then
  if [ "$end" = "now" ]; then

    # If the graph starts a given period ago rather than
    # at a fixed point, then try and modify that.
    case "$start" in
      *ago) start=`zoom_ago in $start` ;;
      *)
        start_sec=$(( start_sec - dur_sec / 2 ))
        start=$start_sec
	;;
    esac

  else
    start_sec=$(( start_sec + dur_sec / 4 ))
    start=$start_sec
    end_sec=$(( end_sec - dur_sec / 4 ))
    end=$end_sec
  fi
fi

if [ "$panleft" ]; then
  start_sec=$(( start_sec - dur_sec / 3 ))
  start=$start_sec
  end_sec=$(( end_sec - dur_sec / 3 ))
  end=$end_sec
fi

echo "start_sec=$start_sec dur_sec=$dur_sec" 1>&2
if [ "$panright" ]; then
  start_sec=$(( start_sec + dur_sec / 3 ))
  start=$start_sec
  end_sec=$(( end_sec + dur_sec / 3 ))
  end=$end_sec
fi

# Produce a watermark for the bottom of the graph. This will
# mark the graph with the date(s) for the data range in case
# we save the image and use it somewhere else later.
#start_date=$(date -d @$start_sec +%d-%b-%Y)
#end_date=$(date -d @$end_sec +%d-%b-%Y)
#if [ "$start_date" = "$end_date" ] ; then
#  watermark="$start_date"
#else
#  watermark="$start_date -> $end_date"
#fi
#GRAPHOPTS="$GRAPHOPTS -W '$watermark'"

# Provide an explicit date format so that we get the same as what we've historically
# explected from Sidious, as 'date' has changed its mind on the default format since.
# The image map javascript expects a fixed format here, so we need to play nice.
start_date=`date -d @$start_sec "+%a %b %d %H:%M:%S %Z %Y"`
end_date=`date -d @$end_sec "+%a %b %d %H:%M:%S %Z %Y"`

[ "$start" != "$start_sec" ] || start=$start_date
[ "$end" = "now" ] || end=$end_date
[ "$stopfollow" ] && end=$end_date

if [ "$png" = "" -a "$dat" = "" ]; then
  if [ "$end" = "now" ]; then
    cat <<EOF
Content-type: text/html
Pragma: no-cache
Refresh: 30

EOF
  else
    cat <<EOF
Content-type: text/html
Pragma: no-cache

EOF
  fi

# We need to state what graphs are currently being shown so that 
# clicking the various fixed timescale links "remember" what we're
# looking at.
  #CURR_GRAPHS="graph1=$graph1&graph2=$graph2&graph3=$graph3&graph4=$graph4"
  CURR_GRAPHS="graph1=$graph1&graph2=$graph2"

cat <<EOF

<HTML>
<HEAD>
  <TITLE>Water Heater Graph Statserv</TITLE>
  <SCRIPT SRC="../image_map.js" LANGUAGE="javascript" TYPE="text/javascript"></SCRIPT>
</HEAD>
<BODY BGCOLOR="$COLOR_BG" TEXT="$COLOR_FG" LINK="$COLOR_LINK" VLINK="$COLOR_LINK">
<FORM NAME=theform>
<TABLE BORDER=0 CELLPADDING=0 CELLSPACING=1 BGCOLOR=$COLOR_PANEL>
<TR>
  <TD WIDTH=20%>
    <B>
    <A HREF="$SCRIPT_NAME?start=1+hour+ago&$CURR_GRAPHS">Last&nbsp;Hour</A> |
    <A HREF="$SCRIPT_NAME?start=4+hours+ago&$CURR_GRAPHS">4&nbsp;Hours</A> |
    <A HREF="$SCRIPT_NAME?start=12+hours+ago&$CURR_GRAPHS">12&nbsp;Hours</A> |
    <A HREF="$SCRIPT_NAME?start=1+day+ago&$CURR_GRAPHS">1&nbsp;Day</A> |
    <A HREF="$SCRIPT_NAME?start=2+days+ago&$CURR_GRAPHS">2&nbsp;Days</A> |
    <A HREF="$SCRIPT_NAME?start=1+week+ago&$CURR_GRAPHS">Week</A> |
    <A HREF="$SCRIPT_NAME?start=1+month+ago&$CURR_GRAPHS">Month</A> |
    <A HREF="$SCRIPT_NAME?start=2+days+ago&end=1+day+ago&$CURR_GRAPHS">Yesterday</A>
    </B>
  </TD>
  <TD>
    <TABLE BORDER=0>
    <TR>
      <TD ALIGN=RIGHT>From:</TD>
      <TD><INPUT TYPE=text NAME=start VALUE="$start" SIZE=28></TD>

      <TD WIDTH=10><INPUT TYPE=submit NAME=plot VALUE=" Apply " DEFAULT></TD>
      <TD ALIGN=RIGHT WIDTH=10><INPUT TYPE=submit NAME=reset VALUE= " Reset "></TD>
      <TD><TABLE CELLPADDING=0 CELLSPACING=0>
        <TR><TD ALIGN=LEFT><FONT SIZE=-1>State: $control_state</FONT></TD></TR>
        <TR><TD ALIGN=LEFT><FONT SIZE=-1>$day_begin &rarr; $day_end</FONT></TD></TR>
      </TABLE></TD>
    </TR>
    <TR>
      <TD ALIGN=RIGHT>To:  </TD><TD><INPUT TYPE=text NAME=end VALUE="$end" SIZE=28></TD>
EOF
if [ "$end" = "now" ]; then
  cat <<EOF
      <TD COLSPAN=2><INPUT TYPE=submit NAME=stopfollow VALUE=" Stop Updating . . . "></TD>
      <TD COLSPAN=2><FONT SIZE=-1>Last Update `date +%R:%S`</FONT></TD>
EOF
else
  cat <<EOF
      <TD WIDTH=20><INPUT TYPE=submit NAME=follow VALUE="  Follow Current  "></TD><TD></TD>
EOF
fi
cat<<EOF
    </TR>
    </TABLE>
  </TD>
</TR>
</TABLE>

<!-- Content table -->
<TABLE BORDER=0 CELLPADDING=0 CELLSPACING=1 BGCOLOR=$COLOR_PANEL WIDTH=100%>
<TR>
  <TD WIDTH=100% ALIGN=CENTER VALIGN=TOP>
    <!-- Graph 1 goes here... -->
EOF
  generate_pulldown graph1
  echo "<p>"
  generate_graph $graph1

cat<<EOF
  </TD>
</TR>
<TR>
  <TD ALIGN=CENTER BGCOLOR=$COLOR_PANEL COLSPAN=2>
  <INPUT TYPE=submit NAME=panleft VALUE=" &lt;- Pan Left ">
  <INPUT TYPE=submit NAME=zoomout VALUE=" Zoom Out (-) ">
  <INPUT TYPE=submit NAME=zoomin VALUE=" Zoom In (+) ">
  <INPUT TYPE=submit NAME=panright VALUE=" Pan Right -&gt; ">
</TD></TR>

<TR>
  <TD WIDTH=100% ALIGN=CENTER VALIGN=TOP>
    <!-- Graph 2 goes here... -->
EOF
  generate_pulldown graph2
  echo "<p>"
  generate_graph $graph2

cat<<EOF
  </TD>
</TR>
 
</TABLE>

</FORM>
</BODY>
</HTML>
EOF
  exit 0
fi

if [ "$png" != "" ]; then
dataset=$png
format=png
cat <<EOF
Content-type: image/png
Pragma: no-cache

EOF
fi

if [ "$dat" != "" ]; then
dataset=$dat
format=dat
cat <<EOF
Content-type: text/plain
Pragma: no-cache

EOF
fi

case "$dataset" in
  water_heater_temps) generate_water_heater_temps $format ;;
  water_tank_temp) generate_water_tank_temp $format ;;
  water_heater_temp_delta) generate_water_heater_temp_delta $format ;;
  host_mem) generate_host_mem $format ;;
  host_temps) generate_host_temps $format ;;
esac

exit 0
