#
# water_heater_common.sh - common definitions for water heater system.
#

####
# CONFIG
#
# Configurable settings.

# Maximum tank temperature that the control script will
# attempt to limit to.
MAX_TANK_TEMP=57.2 # C.
# ** WARNING: SAFETY ** Sticker on side of tank indicates burns
# in seconds at 140F.
#
# The hottest tap is the kitchen sink; everything else is physically
# further away and has higher losses. I'm not too worried about the showers
# as they don't have separate hot/cold knobs (the risk of turning on 100%
# hot water is low), but the bathroom sinks do. The kitchen tap has a mixer,
# but the temptation is to throw it straight on high, and I don't know if
# it allows 100% hot.
#
# On the other hand, some places (such as the UK solar trade association)
# suggest 60C (140F) to kill bacteria in the tank.

# Default times of day where control script will attempt to operate.
# These are fallbacks, overrided by offsets based on sunrise and
# sunset times to manage the varying day length through a year.
CONTROL_DAY_BEGIN="8 am"
CONTROL_DAY_END="5 pm"

# Start and stop times relative to sunrise & sunset. Values are as
# per 'sunwait's offset option, and are in hours:minutes.
# Weirdly, a positive value is added to the sunrise time, but is
# subtracted from sunset.
CONTROL_DAY_SUNRISE_OFFSET="+2:10"
CONTROL_DAY_SUNSET_OFFSET="+2:15"

# To calculate sunrise & sunset times, we need a location.
# Passed to 'sunwait', which seems happy enough to take lat/lon
# positions with N/S and W/E suffixes. Obviously not particularly
# close to home, but more than close enough for figuring out times.
SUNWAIT_POS="21.261944N 157.806044W"

####
# STATUS FILE
#
# Path, etc. for status file produced by control script.

# Current status from control script.
CONTROL_STATUS_FILE="/tmp/water_heater/status"

####
# STATSERV
#
# Paths, etc for statserv info.

# Root path of statserv info here.
SS_PATH=/water_heater

# Values in statserv.
SS_STATUS="$SS_PATH/status"
SS_PUMP_STATE="$SS_PATH/pump_state"
SS_CONTROL_STATE="$SS_PATH/control_state"
SS_DAY_BEGIN="$SS_PATH/day_begin"
SS_DAY_END="$SS_PATH/day_end"
SS_TEMP_TANK="$SS_PATH/temp_tank"
SS_TEMP_PUMP="$SS_PATH/temp_pump"
SS_TEMP_RETURN="$SS_PATH/temp_return"
SS_TEMP_SUPPLY="$SS_PATH/temp_supply"
SS_RES_TANK="$SS_PATH/res_tank"
SS_RES_PUMP="$SS_PATH/res_pump"
SS_RES_RETURN="$SS_PATH/res_return"
SS_RES_SUPPLY="$SS_PATH/res_supply"
SS_VOLT_TANK="$SS_PATH/volt_tank"
SS_VOLT_PUMP="$SS_PATH/volt_pump"
SS_VOLT_RETURN="$SS_PATH/volt_return"
SS_VOLT_SUPPLY="$SS_PATH/volt_supply"

# Comments for each statserv value.
SS_COMMENT_STATUS="General status indication."
SS_COMMENT_PUMP_STATE="[0|1] Boolean pump status."
SS_COMMENT_CONTROL_STATE="Current control loop state"
SS_COMMENT_DAY_BEGIN="Time when day begins (24h format)."
SS_COMMENT_DAY_END="Time when day ends (24h format)."
SS_COMMENT_TEMP_TANK="[C] Temperature measured from water tank."
SS_COMMENT_TEMP_PUMP="[C] Temperature measured at water pump fitting."
SS_COMMENT_TEMP_RETURN="[C] Temperature measured on return from heater panel."
SS_COMMENT_TEMP_SUPPLY="[C] Temperature measured at fitting out of tank to the house."
SS_COMMENT_RES_TANK="[Ohm] Resistance of water tank thermistor."
SS_COMMENT_RES_PUMP="[Ohm] Resistance of pump sensor."
SS_COMMENT_RES_RETURN="[Ohm] Resistance of return line sensor."
SS_COMMENT_RES_SUPPLY="[Ohm] Resistance of house hot water supply line sensor."
SS_COMMENT_VOLT_TANK="[V] Voltage across water tank thermistor."
SS_COMMENT_VOLT_PUMP="[V] voltage across pump sensor."
SS_COMMENT_VOLT_RETURN="[V] Voltage across return line sensor."
SS_COMMENT_VOLT_SUPPLY="[V] Voltage across house supply line sensor."

# Info about host raspberry pi goes here.
SS_PI_PATH="$SS_PATH/pi"

SS_PI_CPU_TEMP="$SS_PI_PATH/cpu_temp"
SS_PI_MEM_AVAIL="$SS_PI_PATH/mem_avail"
SS_PI_MEM_FREE="$SS_PI_PATH/mem_free"

SS_COMMENT_PI_CPU_TEMP="[C] Host RPi CPU temperature."
SS_COMMENT_PI_MEM_AVAIL="[kiB] Host RPi available memory."
SS_COMMENT_PI_MEM_FREE="[kiB] Host RPi free memory."

####
# PUMP CONTROL
#
# PUMP_CONTROL_TYPE must be one of the following:
#   - "kasa": pump turned on and off by kasa wifi plug.
#   - "gpio": pump managed by GPIO-controlled system.
#
# For kasa, PUMP_CONTROL_HOST must declare the hostname or IP address
# of the relevant wifi plug.
#
# For GPIO, PUMP_CONTROL_GPIO must declare the gpio pin number (assuming
# this is on an rPi).
PUMP_CONTROL_TYPE="gpio"

# Address of the kasa plug. Switched to GPIO, not used.
#PUMP_CONTROL_HOST="192.168.0.45"

# Pump control is on this GPIO pin. Chosen because it has no other
# duties listed under any circumstances, and the pin and a ground
# are next to each other at the "bottom" of the GPIO block on the
# "inside" of the board. This makes the likelihood of a wiring oops
# a lot less than picking something in the middle of the block, though
# pin 21 was also an option (the two pins on the very end of the block).
#
# Pinout diagram is splattered everywhere, I used this one:
#
#  https://learn.sparkfun.com/tutorials/raspberry-gpio/gpio-pinout
#
PUMP_CONTROL_GPIO=26

###########################################################
# COMMON FUNCTIONS

# Makes it easier to handle math with pesky floating points.
# Second arg is the number of digits to show, defaulting to
# zero if nothing given. For example:
#
#   `calc "2.1 + 1"` will echo back "3".
#   `calc "2.1 + 1" 0` will also echo "3".
#   `calc "2.1 + 1" 1` will echo "3.1"`
calc ()
{
  local digits="$2"
  [ "$digits" ] || digits=0

  # Using awk to do the calculation as it's easier to
  # force it to print the required number of digits
  # (bc can be all over the place depending on its inputs)
  # and because it'll produce sane output for 0.x values
  # with a leading zero.
  awk "BEGIN { printf( \"%.${digits}f\", $1 ) }"
}
