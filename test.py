import re, arth
import unittest

class TestStringMethods(unittest.TestCase):

    def test_parse_normal(self):
        src = '\tOCaml Debugger version 4.02.3\n\n'
        self.assertEqual(arth.parse_output(src), (src, {}))

    def test_parse_time(self):
        src = 'Time: 53 - pc: 186180 - module Format\n'
        self.assertEqual(arth.parse_output(src), ('', {'time': '53', 'pc': '186180', 'module': 'Format'}))

        src = 'Loading program... Time: 1 - pc: 7344 - module Pervasives\n'
        self.assertEqual(arth.parse_output(src), ('Loading program... \n', {'time': '1', 'pc': '7344', 'module': 'Pervasives'}))

        src = 'Time: 101978\nProgram exit.\n'
        self.assertEqual(arth.parse_output(src), ('Program exit.\n', {'time': '101978', 'pc': None, 'module': None}))

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()