import unittest

from cli import *


class Tests(unittest.TestCase):
    def assertEqualsAfterExpansion(self, expected, input):
        self.assertEquals(expected, Interpreter().expand(input))

    def test_no_expansion(self):
        cases = ['echo abc',
                 '',
                 '$',
                 r"echo \'",  # \'
                 r'echo \"',  # \"
                 r'echo \\',  # \\
                 r'echo oo\o',  # oo\o
                 r'echo \$',  # \$
                 r'echo \$oo',  # \$oo
                 "echo 'meow'",  # 'meow'
                 r"echo '$meow'",  # '$meow'
                 'echo \'"$meow"\'',  # '"$meow"'
                 'echo \'"\'',  # '"'
                 r"echo '\'",  # '\'
                 r"echo '\'''",  # '\'''
                 ''
                 ]
        tricky_cases = [('\'', '\''),
                        ('"', '"'),
                        ('\\\\"', '\\\\"')
                        ]  # they are not correct bash input
        for case in cases:
            self.assertEqualsAfterExpansion(case, case)


if __name__ == '__main__':
    unittest.main()
