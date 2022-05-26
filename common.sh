#
# water_heater_common.sh - common definitions for water heater system.
#

# Current status from control script.
CONTROL_STATUS_FILE="/tmp/water_heater/status"

# Root path of statserv info here.
SS_PATH=/water_heater

# Values in statserv.
SS_STATUS="$SS_PATH/status"
SS_PUMP_STATE="$SS_PATH/pump_state"
SS_TEMP_TANK="$SS_PATH/temp_tank"
SS_TEMP_PUMP="$SS_PATH/temp_pump"
SS_TEMP_RETURN="$SS_PATH/temp_return"
SS_RES_TANK="$SS_PATH/res_tank"
SS_RES_PUMP="$SS_PATH/res_pump"
SS_RES_RETURN="$SS_PATH/res_return"
SS_VOLT_TANK="$SS_PATH/volt_tank"
SS_VOLT_PUMP="$SS_PATH/volt_pump"
SS_VOLT_RETURN="$SS_PATH/volt_return"

# Comments for each statserv value.
SS_COMMENT_STATUS="General status indication."
SS_COMMENT_PUMP_STATE="[0|1] Boolean pump status."
SS_COMMENT_CONT_STATE="Current state of control loop."
SS_COMMENT_TEMP_TANK="[C] Temperature measured from water tank."
SS_COMMENT_TEMP_RETURN="[C] Temperature measured on return from heater panel."
SS_COMMENT_TEMP_PUMP="[C] Temperature measured at water pump fitting."
SS_COMMENT_RES_TANK="[Ohm] Resistance of water tank thermistor."
SS_COMMENT_RES_RETURN="[Ohm] Resistance of return line sensor."
SS_COMMENT_RES_PUMP="[Ohm] Resistance of pump sensor."
SS_COMMENT_VOLT_TANK="[V] Voltage across water tank thermistor."
SS_COMMENT_VOLT_RETURN="[V] Voltage across return line sensor."
SS_COMMENT_VOLT_PUMP="[V] voltage across pump sensor."

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
