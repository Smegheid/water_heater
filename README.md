# Solar Water Heater Control Kludge

This is a small set of scripts that I'm throwing together to manage control of the pump on the solar water heater system we have at home, and as a result the temperature of the water in the tank. Because of the very particular set of circumstances involved,

I've set up a repository for this on github for my own convenience. I'm not sure this will be of use to anyone, but if you want to use it, then go right ahead. Since this is public, I figured I should at least pen some deranged ramblings about what's going on.

## Rationale

The summary of the situation is as follows. The existing system was controlled by a Goldline GL-30 controller which controls a little pump to push water from the tank up to the panel on the roof and back to the tank. The controller takes 2 inputs:
    * One 10k thermistor for tank temperature.
    * One 10k thermistor for panel temperature.

The tank temperature sensor is fine, but the panel sensor (or its wiring) is busted. Sometimes it reads somewhat reasonable-looking values, and some times it reads hundreds of kOhms or even several MOhms, which is hideously beyond any semlance of sanity. These values were persuading that the panel was almost always cold even on the sunniest day, so the pump wasn't being turned on.

Running the pump all of the time during the day isn't an option. On cloudy days, whatever heat in the tank may be dumped back to the air via the panel, and on sunny days the water would get to scalding levels fairly rapidly.

Queries sent to local companies for an estimate were either ignored or had ridiculous call-out fees before any work was done. I don't mind paying the going rate, but you're having a laugh if you want that much just to turn up.

Since I already had a raspberry pi to spare and had a wifi remote plug on hand (the pump is rated at all of 85W and has a standard 3-prong plug) , I figured that I could test whether I could kludge something together that would tell me if I could work around the missing sensor or if I had to just bite the bullet and pay the fee.

## Hardware

The system started out with a raspberry pi that was unused, and a Kasa HS105 plug. Because we all love hacking, linux control of these plugs is a mere [pip install](https://python-kasa.readthedocs.io/en/latest/) away. The wifi plug was soon abandoned in favour of a relay that can be controlled via GPIO=, but more on that later.

The only equipment i had to buy to start experimenting was:
  - An A/D converter hat (I settled on the [Pi-16ADC](https://alchemy-power.com/pi-16adc/)).
  - A handful of 10k resistors (went with 1/4W, 1%).
  - Some cheap 10k thermistors from ebay.

The A/D converter hat was chosen for its 16-bit resolution and the little breadboard areas that looked like they would make hooking things up far easier than a separate breadboard with wires everywhere. This space was used to set up a few simple voltage dividers, one for each A/D channel, and the screw terminals made hooking everything up really easy. The example python script for reading back the A/D converter was good enough that I used it as a basis for sampling rather than doing anything fancier. The end results are close enough to what looks like reality that I don't care too much about calibration, etc.

Translation from the A/D voltages to temperature is done as simply as I could think of:
  - As an intermetidate step, the resistance of the thermistors is figured out from Ohm's law. The divider is dead simple, with the fixed 10k resistor on top connected to the positive supply, the thermistor on the bottom connected to gorund, and the A/D measuring the midpoint.
  - Conversion from resistance to temperature came from the python [thermistor-utils](https://pypi.org/project/thermistor-utils/) module, and their example code was invaluable.
    - One note: the example coefficients were well off from what I was seeing in experimentation and from the documentation for the existing controller.  found a set (here)[https://www.skyeinstruments.com/wp-content/uploads/Steinhart-Hart-Eqn-for-10k-Thermistors.pdf] that match the table in the manual exactly and seem to correspond fairly closely to temperatures I was able to test against.

### Sensor Placement

At the time of writing, the system reads back four temperatures, though at the moment it's only really using two. Since the goal was not to mess with the plumbing, I ended up using a little thermal paste and taping thermistors to the following tank fittingts:
  * The return line from the roof panel,
  * The line out of the tank where the pump is connected to send water to the roof,
  * The hot water line out of the tank that supplies the house.

The fittings are all brass, so while they're not 100% accurate to the temperature of the water flowing through them, they're close enough.

At this time, only the existing tank thermistor and the sensor on the return line are used.

### Pump Control

To get things up and running for the initial experiments, a Kasa wifi plug was used as I had one lying around. I fell out of love with this fairly quickly as wifi coverage to the cupboard with the tank and pump isn't brilliant, and with both the rasperry pi and the plug on wifi, that gave attempts to control the plug two ways to fail. For early testing this was fine; the plug was about 99% reliable in terms of being able to be controlled when needed. However, that last 1% was a pain, and the dropouts were often many minutes long. If the tank were hot by midday, these outages could result in overshooting the target temperature by a couple of degrees Celsius, taking the water from hot to dangerous.

That didn't sit right, so I ordered one of DLI's [IoT Relays](https://dlidirect.com/products/iot-power-relay) via Amazon. We've used their web power switches at work for years, and this seemed like a far better idea than trying to cobble something together from parts. With this, the mains side of the system is build from commercial products without hacking up cables or anything, and the pi is on the end of an optoisolator, so the hackery is all low-voltage.

This was trivial to get up and running. It took no time to connect it to the pi's GPIO header (but more time to realise I'd gotten the polarity wrong!) and I've decided to just script control through sysfs as it's more than good enough for an on/off control.

The other reason for switching to GPIO is that if the pi dies or reboots, the GPIO pin will no longer be asserted and the pump will stop.

## Software Control

At the moment, the control loop is a simple state machine implemented as a shell script. Once I'm happy with it I may end up recreating it in python just for the practice, but this is reasonable enough.

The biggest consideration for the control script was to not rely on anything on the network. The  wifi connection for the pi is ok and is more stable than the wifi plug's was, but I don't want to rely on it. As such, the control loop is not allowed to touch anything over the network that could block in any way; even if the wifi goes out completely, it should always continue to run and stay in control of the pump.

With that in mind, status reporting is handled by writing a text file to tmpfs that is then picked up, parsed and used by a separate process to report to the outside world what's going on. This is a little unwieldy, but show be far more repeatable than relying on external resources.

The current state machine is the result of observation and testing. The biggest impediment to making decisions is the missing panel sensor; with the pump off, the system has no way to know whether the panel is capable of heating water.

Several different ideas were tried. For example, when the tank is cold, the return temperature does actually rise as the sun comes up and heats the panel even with the pump off. There can be nearly 10C difference between the tank temperature and the return if the tank is cold. However, if the tank is anywhere near the temperature target, this relationship goes completely out the window; with the pump off, the return will be many degrees below the tank. This is true even at midday with the sun blazing on the panel; turning on the pump shows a burst of scalding hot water (often 80C or more if the system has been left stagnant for a while) yet the mechanism that conducts heat down from the roof when cold breaks down when the tank is hot. I don't have enough information about the components to say why this is the case.

So far, the most effective method I've come up with is to speculatively run the pump if it's turned off. When started, if the panel's capable of heating there's a large spike in temperature at the return fitting within 10-20 sec of starting up. Waiting for a few cycles before making a decision on whether the panel can make hot water seems to work pretty well.

Once running, the decision on whether to keep pumping doesn't seem to need to be more complicated than checking that the return is hotter than the tank. Full sun at midday typically shows around a 3C delta between the tank and the return, and the temperature readings are quiet enough that a simple count of a few consecutive periods where the return is colder than the tank is good enough; it keeps the system running through periods of small clouds passing, and shuts down when the shade is more prolonged.

More surprising is that this appears to work even on partially overcast days. Some days have either a haze or a layer of really thin cloud hanging around for most of the day, yet while the temperature delta reflects this, it's still able to heat the water quite effectively. Even with a delta of about 1C, the tank comes close to its target by the end of the day.

In order to prevent too many sleculative pump cycles wasting heated water from the tank during cloudy periods, I borrowed a page from TCP and threw together an exponental back off arrangement. A delay follows the pump being turned off, and that delay is doubled each time the pump is started then stopped. If the system pumps continuously for a reasonable length of time, the delay is reduced linearly until it's back at the initial time. This way, prolonged periods of cloud will result in the pump being poked less and less often, and continuous sunshine will result in a short delay for the first cloud that comes by.

On top of that, the system enters a dormant state where it will always turn the pump off and will not even consider pumping between a fixed time before sunset until a set time in the morning. I had originally intended this to be tied more closely to the sunrise & sunset times (and might still do so) but the timer on the electrical tank heater operates on fixed times that I don't want to mess with, so fixed times for this might make sense. We'll see if I change my mind later on in the year.

## Reporting

All of the data tracking is done through RRD databases and `rrdgraph`. However, the connection between the control script and the data ending up in the RRDs probably won't make much sense to an outside observer, especially as none of that is supplied with this project. It's all built around software I use at work, which is based on a shared namespace and associated tools that were invented at [CFHT](https://software.cfht.hawaii.edu/). I recognise that this is all quite esoteric and niche, but I've worked with this stuff long enough that I can throw a working system together in a very short amount of time, and I don't care too much about whether it's of use elsewhere.

The graphing script is a simple CGI job that allows for two graphs to be displayed, for panning and zooming, and for automatic updates of a given period. It's not pretty, but it works. This is served by an instance of `busybox` wearing its `httpd` hat as a simple web server.

If anyone reading this is dead set on using this, then it's probably better to just take the control script and add your own reporting interface to the status file that's periodically updated. The file should be fairly self-evident.

## TODO

I'm writing this when the system is in reasonably good shape for the first time. The system turns on in the morning and seems to be capable of monitoring the tank temperature until the target is reached, at which point the pump is turned off. When the tank cools, the pump comes back on and attempts to maintain that level.

However, there are a few things that I'm either not happy with or want to add. I'll probably write up tickets for these, but in no particular order:
  - Software watchdog: I want to set up a separate watchdog that runs from cron and checks a few things:
    - Is the control process running? If not, restart it.
    - Does the claimed state of the pump match the actual state? If not, restart.
    - Make doubly sure that between sunset and sunrise, the pump should always be off.
  - At the moment, there is no hysteresis on the maximum tank temperature. If the water's hot enough, the pump is turned off. If the tank cools by a tenth of a degree (the current resoltion I've stuck with) the pump is turned on. At first glance this might not be a problem as everything in the system moves so slowly that with a hot tank in the early afternoon the duty cycle on the pump is kept low by the delay after turning off the pump. The worst I've seen so far is where the pump is turned on for a couple of minutes out of every ten or so (the exponential back off currently only applies of the return gets too cold). Still the lack of hysteresis feels wrong, and I'll probably add it.
  - The status reporting side of things still needs work. At the moment it works for populating the RRDs for graphs, but it's a bit clunky. The status updating script is currently run in a loop in a `screen` session, which works for now. However, the longer-term goal is to run this from an `inotify`-based arrangement where it's kicked off every time the file is changed. I'm thinking of doing this with `iwatch`, but I haven't fully thought it through yet.
  - While the ADC hat has been simple to get running and its breadboard area gave a completely self-contained system for the coltage dividers, the part I really hate about it is the range of the A/D converers. Single-ended, they only range from 0 - 2.5V. In what seems like a major oversight for DIY jobs like this, the breadboard area only supplies +5V and ground straight from the host RPi as options. This means that the simple voltage dividers I set up will function down to 25C, at which point they will go off-scale. A far better option would have been for the hat to include a regulator on the board and provide a 2.5V rail so that circuits like this could never exceed the range of the A/D converter, but that's not the case. The current temperature limit is fine here for now (it's summer, and nighttime temps barely make it below 80F) but I'm planning on changing this. I'll probably just run a lead from the +3.3V pin on the pi header to the existing breadboard area. I should be able to sense down to about 3C with that setup; if we ever drop below that here, we've got bigger problems going on as a planet...
