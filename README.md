This repository contains the result of some reverse engineered
information on Aritech burglary alarm panels and some free tools to work
with them.

In particular, this repo contains:
  - Some info about the hardware and working of these panels (including
    photographs of the PCBs): [Hardware/README.md](Hardware/README.md)
  - Some info about recovering lost access codes, even when the
    engineering lock is set: [See below](#circumventing-engineer-lock)
  - Documentation about the protocol used between the panel and the
    display units: [Display Protocol.md](Display%20Protocol.md)
  - A python script to emulate the a display unit using an RS232 port,
    to control the panel from your PC: [tools](tools)
  - A python script to automatically try access codes, to find lost
    codes again: [tools](tools)
  - Some (mostly Dutch) manuals about some of these boards: [Manuals](Manuals)

The protocol documentation and python scripts heavily build on
information from [CastleAritechArduinoRKP](https://github.com/OzmoOzmo/CastleAritechArduinoRKP), an Arduino
(ESP8266) implementation of the display protocol.

The focus of this repo is the CD15001 panel (which should be nearly
identical to the CD9501) and to a lesser degree also CD6201 and CD3401,
since that is what I happened to have access to. However, a lot of
things are probably also applicable to other Aritech panels, especially
if they also support the same CD3008 panel I used.

If the information or tools in this repository turn out to be useful for
you, let me know! I'm curious to hear if my work is being used, so just
[drop me a mail](mailto:matthijs@stdin.nl) or [leave a comment in this
discussion](https://github.com/matthijskooijman/AritechRevEng/discussions/1).
Thanks!

### Status and history of this repo
I created this repo because I salvaged a CD15001 panel from
a to-be-demolished building. Hoping someone could still put the panel to
use, I put it up for sale, but together with a prospective buyer,
I discovered the panel had an "engineer lock" set, so it could not be
factory reset without the installer code.

Refusing to simply throw away perfectly good electronics just because of
some software lock, I decided to figure out more about the system and
see if I could circumvent this lock. This repository contains the
result: Information collected from various sources, new information from
fiddling with the board's EEPROM, and some new tools.

When I write this, I am about to sell the board I used for testing. This
means I will no longer have access to any hardware, so I will **probably
not maintain this repository actively**. If you have some more
information to add and can put that in a proper pullrequest, I will try
to merge that, but if you want to actively pursue the topic and do
significant additions, feel free to just fork the repo (and let me know,
then I'll add a link to your repo here). If you have questions on any of
this, feel free to use the discussion area of this repository and I (and
maybe others?) will do my best to help you out with my experiences.

### Terminology
In this documentation, I'm using the term "panel" to refer to the main
burglary alarm controller, even though it does not really have a control
panel itself (but this seems to be the common term). This would probably
be called "Centrale" in Dutch.

Then "Display unit" ("Bediendeel" in Dutch) refers to the control units
with a display and buttons that can be used to control the system.

Part numbers are often abbreviated, e.g. CD3401 is referred to as CD34.
I suspect that the last numbers might refer to different
language/regional versions, but I am not quite sure. The CD15001 has an
extra digit, so should probably be abbreviated as CD150, but I usually
just use CD15.

### Factory reset
If you remove the reset jumper and power up the system, it should reset
all settings (panel will probably start up in alarm mode, with the
display beeping). The panels I have

Then "Display unit" ("Bediendeel" in Dutch) refers to the control units
with a display and keys that can be used to control the system.

Then "Display unit" ("Bediendeel" in Dutch) refers to the control units
with a display and keys that can be used to control the system.seen only have a single jumper,
labeled LK1 on the CD15, and JP1 on the CD62 and CD34.

Note this will not work if the engineer lock is enabled (the jumper is just
ignored and the system starts with the current settings), see below for
details.

### Code and engineer lock
For CD34, CD95, CD15, CD43 and CD62:
 - Default user code 1122
 - Default installer code 1278

With all of the above panels, an engineer lock ("installateursblokkering" in
Dutch) can be enabled in the settings. This prevents doing a factory reset with
the jumper, so the only way to do a reset is then through the menu after
entering the installer code (or by [erasing EEPROM](EEPROM.md)).

[This thread](https://www.diynot.com/diy/threads/aritech-cd95-engineers-code-locked-in.278525/)
suggests the code can be read from NVM/EEPROM with an EEPROM reader, but nobody
is specific about where the code is exactly (I found out - see
[EEPROM.md](EEPROM.md). Second page suggests that the code might be
stored in OTP or some other area outside of the EEPROM, since after
finding the code by bruteforcing, swapping the EEPROM with another one
did not change the code (unsure if this was CD95, but probably).
However, this is not consistent with my findings - the codes are stored
in EEPROM and can be seen and reset in there.

## Circumventing engineer lock
I have found three ways to circumvent an engineer lock:
 1. Read the current code from EEPROM.
 2. Erase the EEPROM to force a factory reset.
 3. Automatically try all possible codes to find a working code.

The first two options are the quickest, but require an EEPROM programmer. More
info about these options is in [EEPROM.md](EEPROM.md).

The last option only requires an RS232 port (USB adapter works), but takes a
long time (about one day to try all 4-digit codes, over two months to try all
6-digit codes...). More info about this option in the [tools](tools)
directory.

## License
All content in this repository (except the EEPROM dumps, which I think are not
really copyrightable material and if they are, then I do not have copyright)
is licensed under the ["Beluki" license](https://github.com/Beluki/License/blob/master/Documentation/License):

> Permission is hereby granted, free of charge, to anyone
> obtaining a copy of this document and accompanying files,
> to do whatever they want with them without any restriction,
> including, but not limited to, copying, modification and redistribution.
>
> NO WARRANTY OF ANY KIND IS PROVIDED.
