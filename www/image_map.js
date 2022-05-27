// Turn an javascript day number into an abbreviated 
// day in English.
function day_num_to_str(day_num)
{
  var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ];
             
  if((day_num < 0) || (day_num > 6)) return "";
  return days[day_num]; 
}

// Turn an javascript month number into an abbreviated 
// month in English.
function month_num_to_str(month_num)
{
  var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ];
             
  if((month_num < 0) || (month_num > 11)) return "";
  return months[month_num]; 
}

// Turn an English month into a javascript month number.
function month_str_to_num(month_str)
{
  switch(month_str.toLowerCase())
  { 
    case "jan":
    case "january":
      return 0;
      break;

    case "feb":
    case "february":
      return 1;
      break;

    case "mar":
    case "march":
      return 2;
      break;

    case "apr":
    case "april":
      return 3;
      break;

    case "may":
      return 4;
      break;

    case "jun":
    case "june":
      return 5;
      break;

    case "jul":
    case "july":
      return 6;
      break;

    case "aug":
    case "august":
      return 7;
      break;

    case "sep":
    case "september":
      return 8;
      break;

    case "oct":
    case "october":
      return 9;
      break;

    case "nov":
    case "november":
      return 10;
      break;

    case "dec":
    case "december":
      return 11;
      break;
  }
}

// Tries to make sense of a date passed as a string from the
// web page.
function get_date(date_str)
{
  var d = new Date;

  // Chop up the date strings and try to make sense of it.
  var date_words = date_str.split(" ");

  // There are a few options as far as the passed dates are concerned.
  // They can take one of three possible formats. 
  // 
  // The first is an absolute timestamp along the lines of 
  // "Wed May  5 10:52:26 HST 2010". This can be chopped up into
  // something the javascript date object can handle.
  //  
  // The second is a relative duration of the format "n amount ago", 
  // where n is a positive integer and amount is one of "sec", "min", 
  // "hour", "day", "week", "month" or "year" (or the plural version).
  //
  // The last is "now", which is pretty self-explanatory.
  if(date_words[0] == "now")
  { 
    // Do nothing. The date object above was given the current
    // time and date when initialised.
  }  
  else if(date_words[2].toLowerCase() == "ago")
  { 
    var duration = date_words[0];
    var amount = date_words[1].toLowerCase();

    switch(amount)
    {
      case "sec":
      case "secs":
        // Do nothing. Dealing with seconds right now.
        break;

      case "min":
      case "mins":
        duration *= 60;
        break;

      case "hour":
      case "hours":
        duration *= 60 * 60;
        break;

      case "day":
      case "days":
        duration *= 60 * 60 * 24;
        break;

      case "week":
      case "weeks":
        duration *= 60 * 60 * 24 * 7;
        break;

      case "month":
      case "months":
        // A month is a really vague quantity. Call it 30 days.
        duration *= 60 * 60 * 24 * 30;
        break;

      case "year":
      case "years":
        duration *= 60 * 60 * 24 * 365;
        break;
    }

    // Date object deals with milliseconds.
    d = Number(d) - (duration * 1000);
  }
  else // Absolute date, e.g. "Wed May  5 10:52:26 HST 2010".
  {
    var last = date_words.length - 1;

    var year = date_words[last];

    // There is sometimes a double space between the 
    // date and month, and javascript very helpfully doesn't
    // take it out, resulting in an empty string. The
    // month is either one or two positions to the left of
    // the date.
    if(date_words[last - 4].length > 0)
    {
      var month = month_str_to_num(date_words[last - 4]);
    }
    else
    {
      var month = month_str_to_num(date_words[last - 5]);
    }
    var day = date_words[last - 3];

    // Chop up the time of day.
    var time_of_day = date_words[last - 2].split(":");
    var hour = time_of_day[0];
    var min = time_of_day[1];
    var sec = time_of_day[2];

    d.setFullYear(year, month, day);
    d.setHours(hour);
    d.setMinutes(min);
    d.setSeconds(sec);
  }

  return d;
}

// Given a date, formats a string in the way that appears in the
// From: and To: fields of the graph page, e.g. "Wed May  5 10:52:26 HST 2010".
function get_date_str(date)
{
  return day_num_to_str(date.getDay()) + " " +
         month_num_to_str(date.getMonth()) + " " +
         date.getDate() + " " +
         date.getHours() + ":" +
         date.getMinutes() + ":" +
         date.getSeconds() + " HST " +
         date.getFullYear();
}

// Click handler for a graph. Either results in recentrinhg the graph
// in x at the position of the click, or displays the values for the graph.
function click_to_centre(doc, event, start_date_str, end_date_str, form, graph_name) 
{
  var start_date = new Date;
  var end_date = new Date;
  start_date = get_date(start_date_str);
  end_date = get_date(end_date_str);

  // The graph spans this many msec in x.
  var date_range = Number(end_date) - Number(start_date);

  // Magic numbers for the plot within the graphic. Not quite
  // right for all graphs, not sure about how to fix that.
  var graph_x_start = 62;
  var graph_width = 532;
  var graph_y_start = 16;
  var graph_height = 340;

  var graph_x_end = graph_x_start + graph_width;
  var graph_y_end = graph_y_start + graph_height;
  
  // Nifty way of figuring out where the mouse click happened relative to
  // the origin of the image instead of the page.
  var element = doc.getElementById("clickme" + graph_name);
//  var origin_x = element.offsetLeft;
//  var origin_y = element.offsetTop;
//  var pos_x = event.offsetX?(event.offsetX):event.pageX-origin_x;
//  var pos_y = event.offsetY?(event.offsetY):event.pageY-origin_y;

  //for IE
  if (window.ActiveXObject) 
  {
    var pos_x = window.event.offsetX;
    var pos_y = window.event.offsetY;
  }
  //for Firefox
  else 
  {
    var left = element.offsetParent.offsetLeft;
    var top = element.offsetParent.offsetTop;

    var pos_x = event.offsetX?(event.offsetX):event.pageX-left;
    var pos_y = event.offsetY?(event.offsetY):event.pageY-top;
  }

  // We want to centre the graph around the clicked x position, but only 
  // for clicks inside the area of the graph itself.
  if((pos_x >= graph_x_start) && (pos_x < graph_x_end) &&
     (pos_y >= graph_y_start) && (pos_y < graph_y_end))
  {
    var graph_x = pos_x - graph_x_start;

    // A pixel is worth this many msec in x.
    var msec_per_x = date_range / graph_width;
    
    // How far do we have to move the graph for this click?
    // Figure out pixels, then convert to msec.
    x_move = graph_x - (graph_width / 2);
    msec_move = x_move * msec_per_x;

    // Figure out what the start and end dates are for 
    // this shift. Number() gets the date in msec, by the way.
    var new_start_date = new Date(Number(start_date) + msec_move);
    var new_end_date = new Date(Number(end_date) + msec_move);

    // Generate strings that we can stick on the web page
    // From: and To: fields for the new start and end dates.
    new_end_date_str = get_date_str(new_end_date);
    new_start_date_str = get_date_str(new_start_date);

    // Jam the new dates into the field and push the go button.
    form.start.value = new_start_date_str;
    form.end.value = new_end_date_str;
    form.submit();
  }

  // Clicks below the graph (on the legend or y axis) will take us to 
  // the dump of the values for the graph.
  else if(pos_y >= graph_y_end)
  {  
    location.href = location.href + "&dat=" + graph_name;
  }

}
