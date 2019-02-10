import unittest

from cli import *


def token_to_str(token):
    return ''.join(map(str, token))


class Tests(unittest.TestCase):
    def assertEqualsAfterExpansion(self, expected, input):
        self.assertEquals(expected, Interpreter().expand_identifiers(input))

    def dummy_test_no_expansion(self):
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


class TranslateIntoRichTests(unittest.TestCase):
    def test(self):
        lines = [
            'echo',
            'echo $foo\ bar "\\ foo bar" \\p | echo meow',
            '"inside \' double \\ quotes \'"',
        ]

        interpreter = Interpreter()
        for line in lines:
            rich = interpreter.translate_into_rich_line(line)
            self.assertEqual(line, ''.join(map(str, rich)))


class TokenizeTests(unittest.TestCase):
    def test(self):
        interpreter = Interpreter()
        lines = [
            'echo meow "cat',
            'echo one | echo two',
            '"foo" \\p',
            'echo "meow \\" meow"',
            'echo $foo\ bar \t\n\v\r"\\ foo bar" \\p | echo meow',
            'foo=42',
            'foo = 42',
        ]
        expected_lines = [
            'echo meow "cat'.split(),
            'echo one | echo two'.split(),
            '"foo" \\p'.split(),
            ['echo', '"meow \\" meow"'],
            ['echo', '$foo\ bar', '"\\ foo bar"', '\\p', '|', 'echo', 'meow'],
            ['foo', '=', '42'],
            ['foo', '=', '42'],
        ]

        for line, expected_tokens in zip(lines, expected_lines):
            rich_line = interpreter.translate_into_rich_line(line)
            tokens = interpreter.tokenize(rich_line)
            for token, expected_token in zip(tokens, expected_tokens):
                self.assertEqual(expected_token, token_to_str(token))


class ExpandIdentifiersTests(unittest.TestCase):
    def test(self):
        scope = defaultdict(str)
        scope['foo'] = 'first'
        scope['bar'] = 'second'
        interpreter = Interpreter(scope)
        line_to_expected = {
            'echo': 'echo'.split(),
            'echo $foo': 'echo first'.split(),
            'echo $foo $bar': 'echo first second'.split(),
            'echo $foo$bar': 'echo firstsecond'.split(),
            'echo "$foo"': 'echo "first"'.split(),
            'echo \'$foo\'': 'echo \'$foo\''.split(),
        }

        for line, expected_tokens in line_to_expected.items():
            rich_line = interpreter.translate_into_rich_line(line)
            tokens = interpreter.tokenize(rich_line)
            expanded_tokens = interpreter.expand_identifiers(tokens)

            for expected_token, token in zip(expected_tokens, expanded_tokens):
                self.assertEqual(expected_token, token_to_str(token))


class ParseTests(unittest.TestCase):
    def test(self):
        scope = defaultdict(str)
        scope['foo'] = 'first'
        interpreter = Interpreter(scope)
        line_to_expected = {
            'echo': 'Command(echo, [], None)',
            'echo $foo': 'Command(echo, [first], None)',
            'echo $foo | echo': 'Command(echo, [first], None) | Command(echo, [], None)'
        }
        for line, expected in line_to_expected.items():
            rich_line = interpreter.translate_into_rich_line(line)
            tokens = interpreter.tokenize(rich_line)
            expanded_tokens = interpreter.expand_identifiers(tokens)
            command = interpreter.parse(expanded_tokens)
            self.assertEqual(expected, command.__repr__())


class InterpreterTests(unittest.TestCase):
    def test(self):
        scope = defaultdict(str)
        scope['foo'] = 'first'
        handlers = {'print_args': lambda args, stdin: ' '.join(map(str, args))}
        interpreter = Interpreter(scope=scope, handlers=handlers)
        line_to_expected = {
            'echo $foo': 'first',
            'print_args 30 seconds': '30 seconds',
            'print_args': '',
            'echo $foo | echo': '',
            'bar = 5': '',
            'echo $bar': '5',
        }
        for line, expected in line_to_expected.items():
            actual = interpreter.interpret(line)
            self.assertIsNotNone(actual)
            self.assertEqual(expected, interpreter.interpret(line).strip())


if __name__ == '__main__':
    unittest.main()
