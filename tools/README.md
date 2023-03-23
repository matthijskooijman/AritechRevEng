# Tools for emulating a display unit
This directory contains some python code that can be used to emulate a display
unit. You can run these tools on a regular PC or laptop (or really any platform
that can run Python) and has a RS232 serial port (easiest is a USB RS232
adapter).

There are three files:
 - `display.py` is a tool that interactively emulates a display: It
   shows the screen content that a display unit would show and takes
   keyboard input to send buttonpresses to the panel.
 - `trycodes.py` is a tool that tries all possible access codes, keeping
   track of any codes that might be correct.
 - `protocol.py` is the code that actually implements the protocol and
   is used by the other two files (it should not be called directly, but
   can be used for developing your own tool if needed).

## System requirements
This code has been tested on Linux (Ubuntu). In theory it should be
portable to e.g. Windows and OSX, but this has not been tested (and the
non-standard baudrate might be problematic).

The code requires:
 - Python 3.7
 - The [readchar](https://pypi.org/project/readchar/) python package
   (for `display.py`, not needed for `trycodes.py`). Install with either
   of:
   ```
   sudo apt install python3-readchar
   pip install --user readchar
   ```

## Using `display.py`
To start this tool, open a shell in this directory and simply run
`./display.py` (for linux, or `python3 display.py` on other platforms).

Pass `--help` to get a list of options. In particular, use:
 - `--address` to set the address of the display to emulate. The default
   0 address is usually fine.
 - `--port` to set the serial port to use. The default works for most
   USB-emulated serial ports under linux (assuming you have only one).
 - Various `--print-raw-*` options to print raw data for debugging.

## Using `trycodes.py`
To start this tool, open a shell in this directory and simply run
`./trycodes.py` (for linux, or `python3 trycodes.py` on other
platforms).

By default, this will just start with code 1111 and try every code up to
999999 (which will take over 2 months, see below).

Pass `--help` to get a list of options. In particular, these options are
available:
 - The options documented for `display.py` above.
 - `--first-code` to start at another code (or continue an interrupted
   run).
 - `--progress` to print a message for every code tried.
 - `--print-buttons` and `--print-display-updates` to see exactly the
   input and output (useful to check that communication is happening
   correctly).

When the script finds a (possibly) correct code, it is printed. Also,
when the script is terminated (by pressing ^C, because of an error or
because it is done) it should print a list of (possibly) correct codes
it found. But to ensure any codes found are not lost, it is recommended
to log the output to a file. The easiest is using `tee`. The recommended
way to run this tool is:

    ./trycodes.py --first-code 1111 --progress | tee -i -a trycodes.log

This uses `tee` with `-i` to ignore ^C (to prevent killing tee before it
can log the summary) and `-a` to append in case you need to restart the
process.

## Stability
During testing, I have observed that the panel sometimes stopped
responding, needing a power cycle (and sometimes being off for longer)
to become responsive again. At some point I noticed that the EEPROM chip
was not properly seated in the socket, so that was probably the cause of
these issues (after properly inserting it, it tested 9000 codes without
issues).

## Connecting computer with RS232
The display bus is essentially just a duplex RS232 bus in terms of
voltage and polariy, except that to allow multiple displays, a display
module should probably never actively drive an idle signal.

In practice, you can connect an RS232 port (e.g. USB-to-RS232 adapter)
directly to the panel using the following connections:

| Panel side | RS232 side    |
| ---------- | ------------- |
| A: 12V     | Not connected |
| B: GND     | GND           |
| C: RX      | TxD           |
| D: TX      | RxD           |

A direct connection works, no additionaly components needed.

For debugging and development, it can be handy to also connect the
original display unit to see its view on the display contents. If you
do, connect A/B/D to both the RS232 and display unit, but **make sure
C is connected to only one of them**, otherwise both will be
transmitting on the same line and things will break.

Note that you could also use a USB-to-UART converter (or UART pins on
a raspberry pi or other SBC) that uses TTL UART instead of RS232, but
then you need some circuitry to translate the voltage levels and invert
the signal. For example, the circuit [suggested by the CastleAritech
project](https://github.com/OzmoOzmo/CastleAritechArduinoRKP/blob/master/HowTo/TheOptionalCircuitToBuild.png)
should work for that.

## Baudrate
The baudrate used by this bus is 1953 (512μs/bit), which is a very
non-standard baudrate. Under Linux, not all (combinations of) serial
hardware and serial terminal software supports non-standard baudrates.

This setup has been tested with a PL2303 USB-to-RS232 converter, which
supports the baudrate from python (but not using `minicom` or `stty`).

## Bruteforce speed
Trying a single code takes 2-3 seconds (the CD15 seems a little faster
at 1.5 second), plus a 90-second lockout every 10 codes, which adds
another 9 seconds. This means that:

 - There are 9⁴ four-digit codes (because zeros are not valid), so
   trying all of them should take 6561 codes × 12 seconds/code = 22
   hours.
 - There are 9⁵ five-digit codes, so trying all these should take 59049
   codes × 12 seconds/code = 8 days.
 - There are 9⁶ six-digit codes, so trying all these should take 531441
   codes × 12 seconds/code = 74 days.

This time could be improved by automatically forcing a power cycle to
skip the sabotage lockout. This should reduce the time roughly to
a quarter. This powercycling needs some extra hardware (probably a FET
or relay controlled by an RS232 handshaking pin) and has not been
implemented in software, but should be easy if needed. Another slight
improvement could be made by skipping the 0-keypresses before a new
code, and just directly trying a new code as soon as the access denied
message has disappeared.

## Entering codes
Here are some observations about how the panel processes access codes.
 - After submitting a code, the panel shows a response about 4-5s
   after the last keypress, except for 6-digit codes and correct codes,
   then a response is returned immediately.
 - After 10 invalid codes, the display shows 'Kode Sabotage89', with the
   number counting down‚ refusing new tries for 90 seconds.
 - While the display show "No access" ("Geen toegang"), it does not
   accept new codes.
 - A new code can be submitted directly when the display is idle, but
   you can also first press "0" to cancel any pending prompts or codes.
   When pressing "0" when idle, the display will ask for a code (but
   this "0" can be omitted.
