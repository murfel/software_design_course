import subprocess

from enum import Enum, auto
from collections import defaultdict



class SuperChar:
    special_meaning_when_escaped = 'ntvr \\\'"'

    def __init__(self, char, is_escaped = False):
        self.char = char
        self.is_escaped = is_escaped

    def __repr__(self):
        if self.is_escaped:
            return f'\\{self.char}'
        else:
            return self.char

    def isspace(self):
        return not self.is_escaped and self.char.isspace()

    def issinglequote(self):
        return not self.is_escaped and self.char == '\''

    def isdoublequote(self):
        return not self.is_escaped and self.char == '"'

    def isquote(self):
        return self.issinglequote() or self.isdoublequote()

    def ispipe(self):
        return not self.is_escaped and self.char == '|'

    def isequalsign(self):
        return not self.is_escaped and self.char == '='

    def isquotequotepipe(self):
        return self.isquote() or self.ispipe()

    def isspecial(self):
        return self.isspace() or self.isquotequotepipe()

    def isdollar(self):
        return not self.is_escaped and self.char == '$'

    def isidchar(self):
        if self.is_escaped and self.char in SuperChar.special_meaning_when_escaped:
            return False
        return self.char.isalnum() or self.char == '_'

    def isidfirstchar(self):
        if self.is_escaped and self.char in SuperChar.special_meaning_when_escaped:
            return False
        return self.char.isalpha() or self.char == '_'


class Interpreter:
    class Command:
        def __init__(self, name=None, arguments=None, stdin=None, next_command=None,
                     handlers=None):
            self.name = name
            self.arguments = arguments if arguments else []
            self.stdin = stdin
            self.next_command = next_command
            self.handlers = handlers
            self.handler = None

        @staticmethod
        def token_to_str(token):
            return ''.join(map(str, token))

        def __repr__(self):
            return f'Command({self.token_to_str(self.name)}, ' \
                   f'[{", ".join(map(self.token_to_str, self.arguments))}], {self.stdin})' +\
                   (f' | {self.next_command}' if self.next_command is not None else '')

        def run(self):
            if self.token_to_str(self.name) == 'exit':
                raise Exception('Exit')
            if self.name and self.handlers:
                raw_name = self.token_to_str(self.name)
                if raw_name in self.handlers:
                    self.handler = self.handlers[raw_name]

            if self.handler:
                output = self.handler(list(map(self.token_to_str, self.arguments)), self.stdin)
            else:
                command = [self.token_to_str(self.name)]
                for token in self.arguments:
                    command.append(self.token_to_str(token))
                output = subprocess.run(command, capture_output=True).stdout
                output = output.decode()
            if self.next_command:
                self.next_command.stdin = output
                output = self.next_command.run()
            return output

    def __init__(self, scope=None, handlers=None):
        self.scope = scope if scope else defaultdict(str)
        self.handlers = handlers

    @staticmethod
    def token_to_str(token):
        return ''.join(map(str, token))

    class QuoteState(Enum):
        OUTSIDE_QUOTES = auto()
        INSIDE_SINGLE = auto()
        INSIDE_DOUBLE = auto()

    @staticmethod
    def is_id_char(char):
        return char.isalnum() or char == '_'

    @staticmethod
    def is_id_first_char(char):
        return char.isalpha() or char == '_'

    ESCAPE_CHARACTER = '\\'

    def translate_into_rich_line(self, line):
        # translate raw line into line with rich chars
        new_line = []
        state = self.QuoteState.OUTSIDE_QUOTES

        i = 0
        while i < len(line):
            is_escaped = False
            if line[i] == '\\'and state in [self.QuoteState.OUTSIDE_QUOTES,
                                            self.QuoteState.INSIDE_DOUBLE]:
                if i == len(line) - 1:
                    raise Exception('Incorrect line: ends with an escape character')
                is_escaped = True
                i += 1
            elif line[i] == '\'' and self.QuoteState.OUTSIDE_QUOTES:
                state = self.QuoteState.INSIDE_SINGLE
            elif line[i] == '\'' and self.QuoteState.INSIDE_SINGLE:
                state = self.QuoteState.OUTSIDE_QUOTES
            elif line[i] == '"' and self.QuoteState.OUTSIDE_QUOTES:
                state = self.QuoteState.INSIDE_DOUBLE
            elif line[i] == '"' and self.QuoteState.INSIDE_DOUBLE:
                state = self.QuoteState.OUTSIDE_QUOTES

            new_line.append(SuperChar(line[i], is_escaped))
            i += 1
        return new_line

    def tokenize(self, line):
        # kind of 'split' by space, single & double quotes, pipe, and the = sign
        tokens = []
        state = self.QuoteState.OUTSIDE_QUOTES
        token = []
        i = 0

        def superchar_to_state(superchar):
            if superchar.issinglequote():
                return self.QuoteState.INSIDE_SINGLE
            elif superchar.isdoublequote():
                return self.QuoteState.INSIDE_DOUBLE
            else:
                raise Exception('The char is not a quote')

        while i < len(line):
            if state == self.QuoteState.OUTSIDE_QUOTES:
                if line[i].ispipe():
                    if token:
                        tokens.append(token)
                    tokens.append([line[i]])
                    token = []
                elif line[i].isquote():
                    if token:
                        tokens.append(token)
                    token = [line[i]]
                    state = superchar_to_state(line[i])
                elif line[i].isspace():
                    if token:
                        tokens.append(token)
                        token = []
                    else:
                        pass
                elif line[i].isequalsign():
                    if token:
                        tokens.append(token)
                        token = []
                    tokens.append([line[i]])
                else:
                    token.append(line[i])
            else:
                token.append(line[i])
                if line[i].isquote():
                    state = self.QuoteState.OUTSIDE_QUOTES
                    tokens.append(token)
                    token = []
            i += 1
        if token:
            tokens.append(token)
        return tokens

    def expand_identifiers(self, tokens):
        new_tokens = []
        for token in tokens:
            new_tokens.append(self.expand_identifiers_in_token(token))
        return new_tokens

    def expand_identifiers_in_token(self, token):
        if token[0].char == "'":
            quote_state = self.QuoteState.INSIDE_SINGLE
        elif token[0].char == '"':
            quote_state = self.QuoteState.INSIDE_DOUBLE
        else:
            quote_state = self.QuoteState.OUTSIDE_QUOTES

        class ExpState(Enum):
            NOTHING = auto()
            ATE_DOLLAR = auto()
            EATING_ID = auto()

        state = ExpState.NOTHING
        i = 0
        new_token = []
        current_id = None
        while i < len(token):
            if state == ExpState.NOTHING:
                if token[i].isdollar() and quote_state != self.QuoteState.INSIDE_SINGLE:
                    state = ExpState.ATE_DOLLAR
                    current_id = ''
                else:
                    new_token.append(token[i])
            elif state == ExpState.ATE_DOLLAR:
                if token[i].isidfirstchar():
                    current_id += token[i].char
                    state = ExpState.EATING_ID
                else:
                    current_id = None
                    state = ExpState.NOTHING
            elif state == ExpState.EATING_ID:
                if token[i].isidchar():
                    current_id += token[i].char
                else:
                    new_token.extend(map(SuperChar, self.scope[current_id]))
                    current_id = None
                    state = ExpState.NOTHING
                    i -= 1
            else:
                raise Exception('Internal error: unknown state {}'.format(state))
            i += 1
        if state == ExpState.EATING_ID:
            new_token.extend(map(SuperChar, self.scope[current_id]))
        return new_token

    def parse(self, tokens):
        root_command = self.Command(handlers=self.handlers)
        command = root_command
        i = 0
        while i < len(tokens):
            if tokens[i][0].ispipe():
                raise Exception('Syntax error near unexpected token |')
            else:
                if i + 1 < len(tokens) and tokens[i + 1][0].isequalsign():
                    if i + 2 >= len(tokens):
                        raise Exception('Incorrect assignment: no right-hand-side expression')
                    self.scope[self.token_to_str(tokens[i])] = self.token_to_str(tokens[i + 2])
                    i += 3
                    continue
                command.name = tokens[i]
                i += 1
                command.arguments = []
                while i < len(tokens) and not tokens[i][0].ispipe():
                    command.arguments.append(tokens[i])
                    i += 1
                if i < len(tokens):  # then tokens[i] is a pipe
                    command.next_command = self.Command(handlers=self.handlers)
                    command = command.next_command
                    i += 1
        return root_command if root_command.name else None

    def interpret(self, line):
        line = self.translate_into_rich_line(line)
        line = self.tokenize(line)
        line = self.expand_identifiers(line)
        command = self.parse(line)
        return command.run() if command else ''


def main():
    interpreter = Interpreter()
    line = True
    while line:
        line = input('> ')
        output = interpreter.interpret(line)
        print(output.strip())



if __name__ == '__main__':
    main()
