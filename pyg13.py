#!/usr/bin/env python
import usb.core
import usb.util
import os
import select
import commands
import actions

G13_VENDOR_ID = 0x046d
G13_PRODUCT_ID = 0xc21c
G13_NUM_KEYS = 40
G13_NUM_MODES = 4


G13_KEYS = (["G%d" % x for x in range(1, 23)] +
            ["UNDEF1", "LIGHT_STATE", "BD"] +
            ["L%d" % x for x in range(1, 5)] +
            ["M%d" % x for x in range(1, 4)] +
            ["MR", "LEFT", "DOWN", "TOP", "UNDEF3", "LIGHT", "LIGHT2", "MISC_TOGGLE"])

G13_KEYS = ["G13_KEY_%s" % x for x in G13_KEYS]


LIBUSB_REQUEST_TYPE_STANDARD = (0x00 << 5)
LIBUSB_REQUEST_TYPE_CLASS = (0x01 << 5),
LIBUSB_REQUEST_TYPE_VENDOR = (0x02 << 5)
LIBUSB_REQUEST_TYPE_RESERVED = (0x03 << 5)
LIBUSB_RECIPIENT_DEVICE = 0x00
LIBUSB_RECIPIENT_INTERFACE = 0x01,
LIBUSB_RECIPIENT_ENDPOINT = 0x02
LIBUSB_RECIPIENT_OTHER = 0x03


class G13Device(object):
    def __init__(self, device):
        self.device = device
        self.device.set_configuration()
        # TODO: do we need to manually claim the interface?

        self.unique_id = "%d_%d" % (self.device.bus, self.device.address)

        self.key_maps = [{} * G13_NUM_MODES]
        self.mode = 0

        self.init_lcd()
        self.set_mode_leds(0)
        self.set_key_color(0, 0, 0)
        # TODO: self.write_lcd(g13_logo)
        # TODO: self.uinput = self.create_uinput()
        self.command_fifo = self.create_command_fifo()

    def init_lcd(self):
        self.device.ctrl_transfer(0, 9, 1, 0, None, 1000)

    def set_mode_leds(self, leds):
        data = [0x05, leds, 0x00, 0x00, 0x00]
        self.device.ctrl_transfer(LIBUSB_REQUEST_TYPE_CLASS | LIBUSB_RECIPIENT_INTERFACE,
                                  9, 0x305, 0, data, 1000)

    def set_mode(self, mode):
        self.set_mode_leds(mode)
        # TODO: implement proper mode handling

    def set_key_color(self, red, green, blue):
        data = [0x05, red, green, blue, 0x00]
        self.device.ctrl_transfer(LIBUSB_REQUEST_TYPE_CLASS | LIBUSB_RECIPIENT_INTERFACE,
                                  9, 0x307, 0, data, 1000)

    def create_command_fifo(self):
        fifo_name = "/tmp/g13_cmd_%s" % self.unique_id
        if os.path.exists(fifo_name):
            os.remove(fifo_name)
        os.mkfifo(fifo_name, 0666)
        self.command_fifo = open(fifo_name, os.O_RDWR | os.O_NONBLOCK)

    def handle_commands(self):
        """ Handle commands sent to the command fifo. """
        ready = select.select([self.command_fifo], None, None, 0)
        if not len(ready[0]):
            return False

        data = self.command_fifo.read()
        lines = data.splitlines()
        for line in lines:
            command = commands.Command.parse_command(line)
            if command:
                command.execute(self)

    def handle_keys(self):
        pass

    def bind_key(self, key, action):
        if key not in G13_KEYS:
            raise Exception("The specified key isn't a known G13 key")
        self.key_maps[self.mode][key] = action

    def cleanup(self):
        # TODO: destroy the device cleanly?
        pass


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="user-mode g13 driver")

    # parser.add_argument("--verbose", "-v", action=store_const, const=bool, default=False, "be verbose")

    args = parser.parse_args()
    return args


def find_devices():
    g13s = []
    devices = usb.core.find(idVendor=G13_VENDOR_ID, idProduct=G13_PRODUCT_ID,
                            find_all=True)
    for device in devices:
        g13s.append(G13Device(device))

    return g13s


def main():
    args = parse_args()

    g13s = find_devices()

    running = True
    while running:
        try:
            for g13 in g13s:
                g13.handle_commands()
                status = g13.handle_keys()
                if not status:
                    running = False
        except KeyboardInterrupt:
            running = False

    for g13 in g13s:
        g13.cleanup()

if __name__ == '__main__':
    main()
