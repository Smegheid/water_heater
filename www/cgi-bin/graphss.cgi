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
# CAMERA 1 FUNCTIONS
generate_water_heater_temps ()
{
  format="$1" ; shift
  draw_title="$1" ; shift

  RRD_FILE="$RRD_DIR/water_heater_temps_lt"
  
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
  set - "$@" "GPRINT:temp_return:LAST:(%4.1lfC)\t"
  set - "$@" "GPRINT:temp_delta:LAST: delta %4.1lfC \t"
  set - "$@" "GPRINT:pump_state:LAST:Pump %.0lf\n"

  # We don't really want to exceed this tank temperature.
  set - "$@" "HRULE:57.77#cc5555"

  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -A -Y --upper-limit 60 --lower-limit 28 - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}

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
  
  # Generate the plot
  #
  case "$format" in
    png) $RRDGRAPH -A -Y - $GRAPHOPTS "$@" ;;
    dat) $RRDFETCH "$RRD_FILE" MAX --start "$start_sec" --end "$end_sec" ;;
  esac
}


###############################################################################
# 2U COMPUTER FUNCTIONS
generate_server_temps () {
  CAM="$1" ; shift
  format="$1" ; shift
  draw_title="$1" ; shift

  case "$CAM" in
    h2rg)  RRD_FILE="$RRD_DIR/computers_dlcam1_server_temps_lt" ;;
    h2rg2) RRD_FILE="$RRD_DIR/computers_dlcam2_server_temps_lt" ;;
    *)
      echo "error: No server temp RRD for $CAM."
      exit 1
      ;;
  esac

  set - --start "$start_sec" --end "$end_sec"

  if [ "$draw_title" == "draw_title" ] ; then
    set - --title="$GRAPH_TITLE_server_temps"
  fi

  # Add definition for micropirani pressure.
  #
  set - "$@" "DEF:cpu_temp=$RRD_FILE:cpu_temp:MAX"
  set - "$@" "DEF:disk_temp=$RRD_FILE:disk_temp:MAX"
  set - "$@" "DEF:sys_temp=$RRD_FILE:sys_temp:MAX"
  set - "$@" "DEF:vrm_temp=$RRD_FILE:vrm_temp:MAX"

  # Draw a line and label it.
  #
  set - "$@" "LINE2:cpu_temp$color0:CPU"
  set - "$@" "GPRINT:cpu_temp:LAST: (%.0lf C)\t"
  set - "$@" "LINE2:disk_temp$color1:Disk\g"
  set - "$@" "GPRINT:disk_temp:LAST: (%.0lf C)\t"
  set - "$@" "LINE2:sys_temp$color4:System"
  set - "$@" "GPRINT:sys_temp:LAST: (%.0lf C)\t"
  set - "$@" "LINE2:vrm_temp$color3:CPU VRM"
  set - "$@" "GPRINT:vrm_temp:LAST: (%.0lf C)\t"
  
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
water_heater_temp_delta
"
GRAPH_TITLE_water_heater_temps="Water heater temperatures"
GRAPH_TITLE_water_heater_temp_delta="Water heater temperature delta (return - tank)"

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
    start_sec=$(( start_sec - dur_sec / 2 ))
    start=$start_sec
  else
    start_sec=$(( start_sec - dur_sec / 4 ))
    start=$start_sec
    end_sec=$(( end_sec + dur_sec / 4 ))
    end=$end_sec
  fi
fi

if [ "$zoomin" ]; then
  if [ "$end" = "now" ]; then
    start_sec=$(( start_sec + dur_sec / 2 ))
    start=$start_sec
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

if [ "$panright" ]; then
  start_sec=$(( start_sec + dur_sec / 3 ))
  start=$start_sec
  end_sec=$(( end_sec + dur_sec / 3 ))
  end=$end_sec
fi

# Provide an explicit date format so that we get the same as what we've historically
# explected from Sidious, as 'date' has changed its mind on the default format since.
# The image map javascript expects a fixed format here, so we need to play nice.
start_date=`date -d "1970-01-01 UTC +$start_sec sec" "+%a %b %d %H:%d:%S %Z %Y"`
end_date=`date -d "1970-01-01 UTC +$end_sec sec" "+%a %b %d %H:%d:%S %Z %Y"`
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
      <TD ALIGN=RIGHT WIDTH=100%></TD>
    </TR>
    <TR>
      <TD ALIGN=RIGHT>To:  </TD><TD><INPUT TYPE=text NAME=end VALUE="$end" SIZE=28></TD>
EOF
if [ "$end" = "now" ]; then
  cat <<EOF
      <TD COLSPAN=2><INPUT TYPE=submit NAME=stopfollow VALUE=" Stop Updating . . . "></TD>
      <TD><FONT SIZE=-1>Last Update `date +%r`</FONT></TD>
EOF
else
  cat <<EOF
      <TD COLSPAN=2 WIDTH=20><INPUT TYPE=submit NAME=follow VALUE="  Follow Current  "></TD><TD></TD>
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
  water_heater_temp_delta) generate_water_heater_temp_delta $format ;;
#  server_temps) generate_server_temps $CAM $format ;;
esac

exit 0
