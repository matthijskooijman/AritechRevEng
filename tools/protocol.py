import threading
import serial
import typing
import logging
import calendar
import queue


class DisplayContents(typing.NamedTuple):
    display: str
    alarm: bool
    warning: bool
    beep: bool
    showing_date: bool


class AritechDisplay(threading.Thread):
    """
    This class handles talking to an aritech burglary alarm panel,
    emulating a display unit.

    It listens to updates from the panel, and uses the contained
    display instructions to reconstruct the value that should be
    displayed to the user. These updates are put into a queue to be
    consumed by our caller.

    In response to each query, a response is generated. Callers can
    queue button presses, which will then be sent (one by one) in future
    generated responses.
    """

    # This is 512μs per bit
    BAUDRATE = 1953

    class Types:
        # These are just copied from
        # https://github.com/OzmoOzmo/CastleAritechArduinoRKP/blob/master/CastleAritechArduinoRKP/RKP.cpp
        # No clue of they make sense or if they matter
        CD3008 = 0x0  # keypad with buzzer  - works on cd34 and cd72
        CD9038 = 0x4  # Keypad with 4 zones - works on cd34 (TOTEST: if cd72 supported)
        CD9041 = 0x8  # Glassbreak Expander with no keypad - works on cd34 but not cd72(Keypad displays Error)

    DISPLAY_TYPE = Types.CD3008

    class Buttons:
        """ Constants for send_button(). """
        # numbers are just numbers
        UP = 0xb
        DOWN = 0xc
        PANIC = 0xd
        REJECT = 0xe
        ACCEPT = 0xf

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--print-raw-rx-all', action='store_true')
        parser.add_argument('--print-raw-rx', action='store_true')
        parser.add_argument('--print-raw-tx', action='store_true')
        parser.add_argument('--print-raw-display', action='store_true')
        parser.add_argument('--print-buttons', action='store_true')
        parser.add_argument("--print-display-updates", action='store_true')

        parser.add_argument('--address', type=int, default=0, metavar="ADDR",
                            help="Address of display unit to emulate (default: %(default)s)")
        parser.add_argument('--serial-port', type=str, default="/dev/ttyUSB0", metavar="PORT",
                            help="Serial port to open (default: %(default)s)")

    def __init__(self, args, **kwargs):
        super().__init__(**kwargs)
        self.args = args
        self._contents = DisplayContents(display="", alarm=False, warning=False, beep=False, showing_date=False)
        self.content_updates = queue.SimpleQueue()
        self.button_presses = queue.SimpleQueue()
        self.last_button = None

    def run(self):
        """ Main thread entrypoint. """
        with serial.Serial(self.args.serial_port, self.BAUDRATE, timeout=None) as ser:
            for packet in self.read_packets(ser):
                if self.args.print_raw_rx_all:
                    logging.debug("RX: {}".format(packet.hex()))

                expected = sum(packet[0:-1]) & 0xff
                if expected == 0:
                    expected = 1
                actual = packet[-1]

                if expected != actual:
                    logging.error(
                        "Checksum error: {} (expected 0x{:x}, found 0x{:x})".format(packet.hex(), expected, actual)
                    )

                address = packet[0] >> 4
                if address != self.args.address:
                    continue

                if self.args.print_raw_rx:
                    logging.debug("RX: {}".format(packet.hex()))

                response = self.process_packet(packet)
                ser.write(response)

                if self.args.print_raw_tx:
                    logging.debug("TX: {}".format(response.hex()))

    def send_button(self, button):
        """ Queue sending a button press. """
        if button == 0x0:
            button = 0xa
        if self.args.print_buttons:
            logging.debug(f"Button: 0x{button:x}")
        self.button_presses.put(button)

    def button_queue_len(self):
        return self.button_presses.qsize()

    def wait_for_update(self, timeout=None, block=True):
        """ Get an DisplayContents from the queue. """
        try:
            return self.content_updates.get(timeout=timeout, block=block)
        except queue.Empty:
            return None

    def generate_response(self, ack):
        """ Generate a packet in response to a query from the panel. """
        # This resends the last button press when it was not acked
        # XXX: This is not really tested, since the CD15001 under test
        # seems to always send this bit. Maybe this is really a 1-bit
        # sequence number matching the hardcoded "2" in the reply below?
        if ack:
            self.last_button = None

        if self.last_button is None:
            try:
                self.last_button = self.button_presses.get(block=False)
            except queue.Empty:
                pass

        packet = [
            self.args.address << 4 | self.DISPLAY_TYPE | 2,
            self.last_button << 4 if self.last_button is not None else 0,
            0,
        ]
        packet.append(sum(packet) & 0xff)
        return bytes(packet)

    def process_display_bytes(self, display, data):
        """ Process the display bytes extracted from a received packet. """
        idx = 0
        showing_date = False

        while data:
            b = data[0]
            data = data[1:]

            if len(display) < idx:
                display += " " * (idx - len(display))

            if b == 0x1b:
                # Something with foreign character sets?
                pass
            elif b >= 0x80 and b <= 0x8f:
                # Encoded date
                b0 = b
                b1, b2, b3 = data[:3]
                data = data[3:]

                nMonth = (b0 & 0x0f)
                day = (b1 & (128 + 64 + 32)) >> 5
                date = (b1 & (31))

                h1 = (b2 & 0xf0) >> 4
                if h1 == 0x0A:
                    h1 = 0
                h2 = (b2 & 0x0f)
                if h2 == 0x0A:
                    h2 = 0
                m1 = (b3 & 0xf0) >> 4
                if m1 == 0x0A:
                    m1 = 0
                m2 = (b3 & 0x0f)
                if m2 == 0x0A:
                    m2 = 0

                display = "{:<3} {:>2} {:<3} {}{}:{}{}".format(
                    # 0 means sunday, so wrap around
                    calendar.day_abbr[day - 1 % 7],
                    date,
                    calendar.month_abbr[nMonth],
                    h1, h2,
                    m1, m2,
                )
                idx = 0
                showing_date = True

            elif b >= 0x20 and b <= 0x7f:
                # Normal ASCII
                display = display[:idx] + chr(b) + display[idx + 1:]
                idx += 1
            elif b == 0x90:
                display = ""
            elif b >= 0xa0 and b <= 0xaf:
                # Move cursor
                idx = (b & 0xf)
            elif b >= 0xb0 and b <= 0xbf:
                # Blink
                pass
            elif b >= 0xc0 and b <= 0xcf:
                # Move cursor and clear right
                idx = (b & 0xf) - 1
                display = display[:idx]
            elif b >= 0xe0 and b <= 0xff:
                # Special characters
                chars = {
                    1: 'ë',
                    2: 'ÿ',
                    4: '*',
                    5: '↓',
                    6: '↑',  # Assumption
                    7: '→',
                    8: '←',  # Assumption
                }

                c = chars.get(b & 0xf, None)
                if c:
                    display = display[:idx] + c + display[idx + 1:]
                idx += 1
            else:
                print(f"Unknown display byte: 0x{b:x}")

        return (display, showing_date)

    def process_packet(self, packet):
        """ Process a complete packet (excluding the 0x00 packet boundary). """
        display = self._contents.display
        display_bytes = packet[2:-1]

        # This seems to be some sort of keepalive message that is sent
        # about 8 times per second, but it does not seem to be otherwise
        # meaningful)
        if display_bytes != b'\x02\x13':
            if self.args.print_raw_display:
                logging.debug("Display update: {}".format(display_bytes.hex()))

            (display, added_date) = self.process_display_bytes(display, display_bytes)
            # Once a date is printed, keep showing_date true until the
            # actual display contents is printed (since the panel seems to
            # alternate date update messages with mysteriuous "0213" update
            # messages, which should *not* change showing_date).
            showing_date = (self._contents.showing_date and display == self._contents.display) or added_date

            new_contents = DisplayContents(
                display=display,
                alarm=bool(packet[1] & 0x2),
                warning=bool(packet[1] & 0x4),
                beep=not bool(packet[0] & 0x2),
                showing_date=showing_date,
            )

            if new_contents != self._contents:
                self._contents = new_contents
                self.content_updates.put(self._contents)
                if self.args.print_display_updates:
                    logging.debug(self.contents_to_string(new_contents))

        ack = packet[0] & 0x4
        return self.generate_response(ack)

    def read_packets(self, ser):
        """ Read bytes from the given serial port and yield packets (excluding the 0x00 packet boundary). """
        buf = b''
        while True:
            b = ser.read()
            if b == b'\x00':
                if buf:
                    yield buf
                buf = b''
            else:
                buf += b

    def contents_to_string(self, contents):
        return "[{:<16}] [{}{}{}]".format(
            self._contents.display,
            "A" if self._contents.alarm else " ",
            "W" if self._contents.warning else " ",
            "B" if self._contents.beep else " ",
        )
