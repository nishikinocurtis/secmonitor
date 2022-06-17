import threading

class TestingThread(threading.Thread):
    def __init__(self, script):
        threading.Thread.__init__(self)
        self.script = script
    def run(self):
        # assume the test cases are written in Python
        with open(self.script, "r") as F:
            test_text = F.read()
            exec(test_text)