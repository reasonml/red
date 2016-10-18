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

    def test_parse_location(self):
        src = '\032\032M/Users/frantic/.opam/4.02.3/lib/ocaml/camlinternalFormat.ml:64903:65347:before\n'
        self.assertEqual(arth.parse_output(src), ('', {'file': '/Users/frantic/.opam/4.02.3/lib/ocaml/camlinternalFormat.ml',
            'start': '64903', 'end': '65347', 'before_or_after': 'before'}))

        src = '\032\032H\n'
        self.assertEqual(arth.parse_output(src), ('', {'file': None, 'start': None, 'end': None, 'before_or_after': None}))

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()