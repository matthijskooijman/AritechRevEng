#!/usr/bin/env python3

import argparse
import logging
import readchar
import threading

from protocol import AritechDisplay

FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

parser = argparse.ArgumentParser(
    description="Emulate a display, talking to a burglary alarm controller through a serial port, showing display "
                "contents and forwarding keypresses.",
)
AritechDisplay.add_arguments(parser)
args = parser.parse_args()

display = AritechDisplay(args, daemon=True)
display.start()


def printer():
    while True:
        contents = display.wait_for_update()
        print(display.contents_to_string(contents), flush=True)


threading.Thread(target=printer, daemon=True).start()

keymap = {
    '0': 0x0,
    '1': 0x1,
    '2': 0x2,
    '3': 0x3,
    '4': 0x4,
    '5': 0x5,
    '6': 0x6,
    '7': 0x7,
    '8': 0x8,
    '9': 0x9,
    readchar.key.UP: AritechDisplay.Buttons.UP,
    readchar.key.DOWN: AritechDisplay.Buttons.DOWN,
    'p': AritechDisplay.Buttons.PANIC,
    readchar.key.ESC: AritechDisplay.Buttons.REJECT,
    readchar.key.BACKSPACE: AritechDisplay.Buttons.REJECT,
    readchar.key.ENTER: AritechDisplay.Buttons.ACCEPT,
}

print("Available keys: 0-9, ENTER, ESC/BACKSPACE, UP, DOWN, p for panic")

while True:
    key = readchar.readkey()
    button = keymap.get(key, None)
    if button is None:
        logging.error("Unknown key pressed")
        continue

    display.send_button(button)
