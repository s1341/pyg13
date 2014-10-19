import platform
import pykeyboard


class Action(object):
    def perform(self, device, key_state):
        pass

keyboard = pykeyboard.PyKeyboard()

class SendKeyAction(Action):
    def __init__(self, key):
        self.key = key

    def perform(self, device, key_state):
        print "SendKeyAction: ", self.key
        if key_state:
            keyboard.press_key(self.key)
        else:
            keyboard.release_key(self.key)
