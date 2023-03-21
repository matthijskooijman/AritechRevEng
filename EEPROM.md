# EEPROM
These boards use an external (i.e. not integrated in the MCU) EEPROM chip.

See the [EEPROM](EEPROM) directory for some dumps of the contents for some boards.

On the CD15 and CD62 these are nicely put into a socket, which allows pulling them
out and reading them in a separate EEPROM programmer. On the CD34, the EEPROM
chip is soldered onto the board, requiring some soldering to remove it (which I
have not done, so no EEPROM dumps for CD34).

## EEPROM programmer
To read these EEPROM chips, an EEPROM programmer is needed - a piece of
hardware where you can insert the EEPROM chip and that can twiddle the chip's
pins just right to read or change its contents.

I've used a TL866 programmer (which works well under Linux with the
[open-source minipro software](https://gitlab.com/DavidGriffith/minipro)), but
there are a lot of different programmers out there that work (just check that
they have support for the EEPROM chip on your board, see [Hardware/README.md](Hardware/README.md)
for the chips used on some boards - and doublecheck yours, since I would
not be suprised if they used slightly different chips in different
batches of the board).

It should also be doable to build your own EEPROM programmer using an Arduino
or similar microcontroller, but I have not tried this.

## Erasing EEPROM
Erasing the EEPROM (by filling it with 0xff) and then re-inserting the EEPROM
makes the panel work as normal. It writes a new EEPROM content and then
starts with default settings (any engineer lock is disabled by this).

Removing the EEPROM after this (without changing any setting) confirms
that the panel has written default EEPROM contents. Note that if you do
a factory reset (by removing the jumper) after this, it seems a bit more
data is written to EEPROM, so it might be good to always do a factory
reset as well.

The X28HC256 (for CD15) does not seem to have a chip erase command, so erasing can be done
by writing a file with 0x8000 0xff bytes (other boards might need
slightly different commands):

	srec_cat -generate 0x0 0x8000 --repeat_data 0xFF -o Empty.hex -Intel
	minipro -p X28HC256 -w Empty.hex 

## Installer lock
Comparing EEPROM contents with engineer lock enabled and disabled shows quite
some differences. Some of these are probably because of new alarms, log
messages, codes entered and power cycles, but there are couple of bits that
seem to be set when enabling the engineer lock and reset when disabling the
engineer lock again.

I have not further investigated which bit it is exactly, but in case you want
to have a look, here's the EEPROM dumps I made:

1. [EEPROM/CD15001/EEPROM After erase.txt](EEPROM/CD15001/EEPROM%20After%20erase.txt) - Contents after a first boot after erasing the EEPROM.
2. [EEPROM/CD15001/EEPROM Enabled engineer lock.txt](EEPROM/CD15001/EEPROM%20Enabled%20engineer%20lock.txt) -  After a second boot in which the system was disabled and the engineer lock was enabled.
3. [EEPROM/CD15001/EEPROM Disabled engineer lock.txt](EEPROM/CD15001/EEPROM%20Disabled%20engineer%20lock.txt) - After a third boot in which the system was disabled and the engineer lock was disabled again.

## Peeking installer code from EEPROM
Looking at the default [CD15001 EEPROM contents](EEPROM/CD15001/EEPROM%20After%20erase.txt) for the default user code (1122) and installer code (1278) shows they are here:

```
00000500  11 22 00 0d 00 00 01 00  00 00 0d 00 00 01 00 00  |."..............|
...
000007c0  00 00 01 00 00 00 0d 00  00 01 12 78 00 00 04 00  |...........x....|
```

Looking at the same area [in an original system](EEPROM/CD15001/EEPROM%20Original.txt), shows:

```
000004f0  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 9a  |................|
00000500  12 75 90 0d 00 08 01 22  75 90 0d 00 08 02 00 00  |.u....."u.......|
00000510  00 0d 00 00 01 00 00 00  0d 00 00 01 00 00 00 0d  |................|
...
000007b0  00 0d 00 00 01 24 77 00  0d 00 00 03 48 48 00 0d  |.....$w.....HH..|
000007c0  00 00 01 00 00 00 0d 00  00 01 33 64 48 00 04 00  |..........3dH...|
000007d0  ff f2 ff ff ff ff ff 3e  ff ff ff ff ff 3e ff ff  |.......>.....>..|
```
Here, it seems the user code was changed to 12759 and installer code to 336448,
but it also shows additional codes, probably for additional users. It seems
this block contains 7 bytes for each user, with the code in the second, third
and fourth bytes. Unused users are `01 00 00 00 0d 00 00`.

Note that codes can actually be 4-6 digits long according to the manual, unused
digits are 0. At first it seemed the installer code for the above dump was
3364, but it was actually 336448...

In the CD6201, the [EEPROM is more compact](EEPROM/CD6201/EEPROM%20After%20erase.txt) (no ASCII for zone names for
example). After a reset, the default codes can be found here:
```
00000090  11 22 00 0b 00 00 00 0b  00 00 00 0b 00 00 00 0b  |."..............|
000000a0  00 00 00 0b 00 00 00 0b  00 00 00 0b 00 00 00 00  |................|
000000b0  12 78 00 0a 68 01 8a 40  18 07 8a 40 18 06 8a 40  |.x..h..@...@...@|
```
It seems this is 4 bytes for each user instead of 7, and (some bits in) the
last byte probably indicates the user type (0x0b for user, 0x0a for installer).

## EEPROM dumps
In the [EEPROM](EEPROM) directory, I have put dumps of the EEPROM contents of the
boards I have seen, in various circumstances.
