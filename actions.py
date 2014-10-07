import platform


class Action(object):
    def perform(self, device, key_state):
        pass

if platform.uname()[0] == "Darwin":
    class SendKeyAction(Action):
        def __init__(self, key):
            # TODO: convert key into OSX virtual key
            self.key = key

        def perform(self, device, key_state):
            import Quartz

            Quartz.CGEventPost(Quartz.kCGHIDEventTap,
                               Quartz.CGEventCreateKeyboardEvent(None, self.key,
                                                                 key_state))

elif platform.uname()[0] == "Linux":
    class SendKeyAction(Action):
        pass
