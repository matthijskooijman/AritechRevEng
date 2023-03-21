### Display bus protocol
The displays seem to use regular RS232 or at least something compatible with RS232 (connected to GPIO pins on the MCU through resistors and transitors for, I presume, voltage shifting and inverting, no actual RS232 transceiver is used). Arduino code exists that shows that the mainboard sends out queries containing a display address and contents to show on the display, and the display is expected to reply with a four-byte reply including some type code and the key pressed (if any).

The baudrate used is 1953 bps (512μs per bit).

Most of this documentation is based on code by OzmoOzmo, who created some ESP8266/ESP32 Arduino code to emulate a display. For more information, see their [instructable here](https://www.instructables.com/House-Alarm-Internet-Dialer-With-Arduino-Reverse-E/), the [ESP8266 code](https://github.com/OzmoOzmo/CastleAritechArduinoRKP), or the [ESP32 code](https://github.com/OzmoOzmo/CastleAritechArduinoESP32).
#### Panel-to-display
| Byte | Bits | Meaning                                                                           |
| ---- | ---- | --------------------------------------------------------------------------------- |
| 0    | 8:4  | Display address                                                                   |
| 0    | 3    | Unknown                                                                           |
| 0    | 2    | Ack                                                                               |
| 0    | 1    | Panel beep (inverted - when 0: panel starts beeping, when 1: panel stops beeping) |
| 0    | 0    | Unknown                                                                           |
| 1    | 8:3  | Unknown                                                                           |
| 1    | 2    | Warning                                                                           |
| 1    | 1    | Alarm                                                                             |
| 1    | 0    | Unknown                                                                           |
| 2+   |      | Display contents                                                                  |
| n-1  |      | Checksum (sum of bytes 0 - )                                                      |
| n    |      | End-of-frame (0x00)                                                               |

According [to comments](https://github.com/OzmoOzmo/CastleAritechArduinoRKP/blob/c6cecebd3c0001ba6f1559754f9b9897de68fe5b/CastleAritechArduinoRKP/RKP.cpp#L244-L245), CD34 has an additional 0x00 Start-of-frame byte before byte 0, which is not included in the checksum.

Checksum is simply the byte sum of preceding bytes, except when it would be 0x00, then it becomes 0x01.

The ACK bit is a bit unclear. The code suggests the previous key should be resent when the ACK bit is clear, but in practice it seems that the ACK bit is clear on startup and becomes set as soon as a single valid reply from the display was received (and then it stays set, even if the display is disconnected and the panel shows display fault ("RBD storing" in Dutch). 

So maybe this is not an ACK bit at all? It seems that the bit can also become unset when sending a reply that has byte 0 bit 1 *unset* instead of always on as documented below. Maybe this is some kind of 1-bit (toggling) sequence "number" (but the CD3008 display seems to always leave this at 1, so maybe that means it does not support ack/retry?). It also seems that buttonpresses with this bit set at 0 *are* processed by the panel, but always leaving it at 0 triggers a display fault.

The bytes of the display contents are encoded as follows:

| Value     | Meaning                                                                |
| --------- | -----------------------------------------------------------------------|
| 0x20-0x7F | ASCII                                                                  |
| 0x80-0x8F | Encoded date                                                           |
| 0x90      | Clear screen                                                           |
| 0x91      | Home (move cursor to position 0)                                       |
| 0x98 0x9c | Show blinking underline at current position                            |
| 0xA0-0xAF | Move cursor, position in lowest bits                                   |
| 0xB0-0xBF | Blink n characters, n in lowest bits                                   |
| 0xC0-0xCF | Move cursor and clear display right of cursor, position in lowest bits |
| 0xE0-0xFF | Special characters                                                     |

Details can be found [in this code](https://github.com/OzmoOzmo/CastleAritechArduinoRKP/blob/c6cecebd3c0001ba6f1559754f9b9897de68fe5b/CastleAritechArduinoRKP/RKP.cpp#L343-L449).

#### Display-to-Panel
Panel sends messages to multiple displays in turn (seems not to all 16 addresses). Whenever a display receives a message (about every 200ms it seems), it sends a reply containing the key pressed (if any) and some status info (while the panel is already sending a message to the next display). Collision avoidance is probably because displays only respond when polled and always send shorter messages than the panel (so a reply can be sent by the display while the panel is already sending a query to the next display).

| Byte | Bits | Meaning                             |
| ---- | ---- | ------------------------------------|
| 0    | 8:4  | Display address                     |
| 0    | 2:3  | Display type? See [this code](https://github.com/OzmoOzmo/CastleAritechArduinoRKP/blob/c6cecebd3c0001ba6f1559754f9b9897de68fe5b/CastleAritechArduinoRKP/RKP.cpp#L540-L542) |        
| 0    | 1    | Unknown (Always 1?)                 |
| 0    | 0    | Lid tamper switch (0=ok, 1=tamper)  |
| 1    | 8:4  | Key pressed                         |
| 1    | 3:0  | Unknown (0x0)                       |
| 2    |      | Unknown (0x00)                      |
| 3    |      | Checksum over preceding three bytes |
