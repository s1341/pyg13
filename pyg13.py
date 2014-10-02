#!/usr/bin/env python
import usb.core
import usb.util
import os
import select
import commands

G13_VENDOR_ID = 0x046d
G13_PRODUCT_ID = 0xc21c
G13_KEY_ENDPOINT = 1
G13_LCD_ENDPOINT = 2
G13_REPORT_SIZE = 8
G13_LCD_BUFFER_SIZE = 0x3c0
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

        self.key_maps = [{}] * G13_NUM_MODES
        self.key_states = {}
        self.mode = 0

        def dummy_managed_claim_interface(device, intf):
            self.device._ctx.managed_open()

            if isinstance(intf, usb.core.Interface):
                i = intf.bInterfaceNumber
            else:
                i = intf

            if i not in self.device._ctx._claimed_intf:
                # self.backend.claim_interface(self.handle, i)
                self.device._ctx._claimed_intf.add(i)

        self.device._ctx.managed_claim_interface = dummy_managed_claim_interface

        self.init_lcd()
        self.set_mode_leds(0)
        self.set_key_color(0, 0, 0)
        # TODO: self.write_lcd(g13_logo)
        # TODO: self.uinput = self.create_uinput()
        self.create_command_fifo()

    def init_lcd(self):
        self.device.ctrl_transfer(0, 9, 1, 0, None, 1000)

    def set_mode_leds(self, leds):
        data = [0x05, leds, 0x00, 0x00, 0x00]
        self.device.ctrl_transfer(LIBUSB_REQUEST_TYPE_CLASS[0] |
                                  LIBUSB_RECIPIENT_INTERFACE[0],
                                  9, 0x305, 0, data, 1000)

    def set_mode(self, mode):
        self.set_mode_leds(mode)
        # TODO: implement proper mode handling

    def set_key_color(self, red, green, blue):
        data = [0x05, red, green, blue, 0x00]
        self.device.ctrl_transfer(LIBUSB_REQUEST_TYPE_CLASS[0] |
                                  LIBUSB_RECIPIENT_INTERFACE[0],
                                  9, 0x307, 0, data, 1000)

    def create_command_fifo(self):
        self.command_fifo_name = "/tmp/g13_cmd_%s" % self.unique_id
        if os.path.exists(self.command_fifo_name):
            os.remove(self.command_fifo_name)
        os.mkfifo(self.command_fifo_name, 0666)
        self.command_fifo = os.open(self.command_fifo_name, os.O_RDWR | os.O_NONBLOCK)

    def handle_commands(self):
        """ Handle commands sent to the command fifo. """
        ready = select.select([self.command_fifo], [], [], 0)
        if not len(ready[0]):
            return False

        data = os.read(self.command_fifo, 1000)
        print "< %s" % data
        lines = data.splitlines()
        for line in lines:
            command = commands.Command.parse_command(line)
            if command:
                command.execute(self)

    def get_key_state(self, key):
        if key not in self.key_states:
            return False
        return self.key_states[key]

    def set_key_state(self, key, state):
        self.key_states[key] = state

    def get_key_action(self, key):
        return self.key_maps[self.mode].get(key, None)

    def bind_key(self, key, action):
        if key not in G13_KEYS:
            raise Exception("The specified key isn't a known G13 key")
        self.key_maps[self.mode][key] = action
        self.key_states[key] = False

    def handle_keys(self):
        print self.device
        report = self.device.read(0x80 | G13_KEY_ENDPOINT, G13_REPORT_SIZE) #, 1000)

        for g13_key_index, g13_key_name in enumerate(G13_KEYS):
            actual_byte = report[3 + (g13_key_index / 8)]
            mask = 1 << (g13_key_index % 8)
            is_pressed = actual_byte & mask
            # if the key has changed state, we're going to want to perform the action
            if self.get_key_state(g13_key_name) != is_pressed:
                self.set_key_state(g13_key_name, is_pressed)

                action = self.get_key_action(g13_key_name)
                if action:
                    action.perform(self, is_pressed)

    def cleanup(self):
        # TODO: destroy the device cleanly?
        os.close(self.command_fifo)
        os.remove(self.command_fifo_name)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="user-mode g13 driver")

    # parser.add_argument("--verbose", "-v", action=store_const, const=bool,
    # default=False, "be verbose")

    args = parser.parse_args()
    return args


def find_devices():
    g13s = []
    devices = usb.core.find(idVendor=G13_VENDOR_ID, idProduct=G13_PRODUCT_ID,
                            find_all=True)
    print devices
    for device in devices:
        g13s.append(G13Device(device))

    return g13s


def main():
    # args = parse_args()

    g13s = find_devices()

    print g13s
    running = True
    while running:
        try:
            for g13 in g13s:
                g13.handle_commands()
                status = g13.handle_keys()
                # if not status:
                #     running = False
        except KeyboardInterrupt:
            running = False

    for g13 in g13s:
        g13.cleanup()

if __name__ == '__main__':
    main()
