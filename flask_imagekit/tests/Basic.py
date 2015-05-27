import unittest
from time import sleep
from flask_imagekit.signals import *

# A bit of a hack to get around python's closure restrictions
class Result(object):
    result = False

class TestBasicFunc(unittest.TestCase):

    def test_signals(self):

        signals = [content_required, existence_required, source_saved]

        for signal in signals:
            test_result = Result()

            def callback(blah):
                test_result.result = True

            signal.connect(callback)

            signal.send()

            self.assertTrue(test_result.result)

if __name__ == '__main__':
    unittest.main()