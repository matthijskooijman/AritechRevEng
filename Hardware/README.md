# Hardware overview
This file describes some details about a couple of Aritech boards. Also
see the [Photos subdirectory](Photos), which has photographs of a number of
panel and dialer boards, and display units.

## CD15001 board
- CPU is NEC MPD78C10ACW (marked with D78C10ACW).
- EEPROM is marked XICOR X28HC256P-15 HY09907. Seems to be identical to X28C256 (also from Xicor), except HC has 128-byte pages and C has 64-byte pages (and HC is available in faster speed grades). Support in minipro is added [by this merge request](https://gitlab.com/DavidGriffith/minipro/-/merge_requests/221).
- ROM is marked ST M27C512-12B1 (maybe more, I left some of the sticker on there). This probably contains firmware since it is ROM and contains the "CD15001 Ver:6.22" sticker). Supported by minipro as `M27C512@DIP28`.
- SRAM is marked HOLTEK HT6264-70 9919K0373

**Routing of display bus**
 - Terminal 47 via Q2, Q11 and some resistors -> MCU pin 21
 - Terminal 48 via resistor near terminal via resistor near 74hc14 -> Pin 9 input of 74hc14 inverter -> pin 8 output -> MCU pin 20

Note that the MCU pins are GPIOs, not a hardware UART.

**Routing MCU UART**

So where is the MCU hardware UART routed? It connects to the PL4 connector:
 - MCU uart pin 17/18 -> 1k resistor -> ADM232LAN pin 11/12 -> pin 13/14 ->  1k resistor -> PL4 connector middle pins

I have attached a scope to these pins, but there seems to be no output
from them. The board probably only speaks when spoken to, but I have not
idea what the baudrate or protocol is (have not tried anything).

## CD6201 board
 - CPU is NEC MPD78C17CW (marked D78C17CW)
 - EEPROM is marked x24c16p (probably Xicor)
 - Code ROM is National Semiconductor NM27C512Q200 (UV-erasable EPROM)

## CD3401 board
 - CPU is NEC MPD78C17CW (marked D78C17CW)
 - EEPROM is ST marked "CHN L // 24C16 6 // K7C304" (Probably M24C16?). Soldered to the board, not socketed.
 - Code ROM is SST27SF512 (Flash)

## Power supply
The power supply on these boards is documented to accept 17-18V AC, but
at least on the CD15, the pins seem to directly connect to a bridge
rectifier followed by linear voltage regulators, so applying DC should
also work. I've tried applying 12VDC, which seems to work just fine
(probably means the 7812 used outputs a little less than 12V, but it
worked well enough for a little hacking - maybe not ideal for
production).

## ROM contents
The code that runs on these boards is stored in ROM chips (I've seen both real
write-once ROM chips, as well as erasable ones). I have made some dumps of the
ROMs of some boards (CD15001, CD3401, CD6201 and RD6201), but because they
contain code (which is definitely subject to copyright), I have not published
them here. If you have a corrupted ROM chip and need a dump for replacement,
let me know and I can send it to you privately.
