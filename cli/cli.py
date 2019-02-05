import sys
from enum import Enum


class SuperChar:
    def __init__(self, char, is_escaped = False):
        self.char = char
        self.is_escaped = is_escaped

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

    def isquotequotepipe(self):
        return self.isquote() or self.ispipe()

    def isspecial(self):
        return self.isspace() or self.isquotequotepipe()

class Interpreter:
    class Command:
        def __init__(self, name, arguments, stdin):
            pass

        def run(self):
            pass

    def __init__(self):
        self.dict = dict()

    class QuoteState(Enum):
        OUTSIDE_QUOTES = 0,
        INSIDE_SINGLE = 1,
        INSIDE_DOUBLE = 2

    @staticmethod
    def is_id_char(char):
        return char.isalnum() or char == '_'

    @staticmethod
    def is_id_first_char(char):
        return char.isalpha() or char == '_'

    ESCAPE_CHARACTER = '\\'

    def new_expand(self, line):
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

            new_line += SuperChar(line[i], is_escaped)
            i += 1


    def tokenize(self, line):
        # kind of 'split' by space, single quotes, double quotes, and pipe!
        tokens = []
        state = self.QuoteState.OUTSIDE_QUOTES
        token = []
        i = 0
        while i < len(line):
            if not line[i].isspecial():
                pass

    # def tokenize(self, line):
    #     # kind of 'split' by space, single quotes, and double quotes
    #     tokens = []
    #
    #     i = 0
    #     token = []
    #     while i < len(line):
    #         while i < len(line) and not line[i].isspecial():
    #             token += line[i]
    #             i += 1
    #         if line[i].isspace():
    #             tokens.append(token)
    #             token = []
    #         elif line[i].isdoublequote():
    #             tokens.append(token)
    #             token = [line[i]]
    #             while i < len(line) and not line[i].isspecial():
    #                 token += line[i]
    #                 i += 1
    #         elif line[i].ispipe():
    #             tokens.append(token)
    #             tokens.append(line[i])
    #             token = []
    #         while i < len(line) and line[i].isspace():
    #             i += 1
    #     tokens += token

    def parse(self, tokens):
        pass






    def expand(self, line):
        """
        Expand variables (identifiers preceded by the dollar sign $) outside of quotes
        and inside of double quotes and do not expand outside of single quotes.

        This preserves meaningless escapes. E.g. if a character without special meaning is escaped,
        both the escape and the character get into the return string.

        :param line: a line to expand variables in
        :return: a line after one level of variable expansion (i.e. after one sweep)
        """

        new_line = ''
        state = self.QuoteState.OUTSIDE_QUOTES
        current_variable = None

        line = list(line)
        for prev_char, char, next_char in zip([None] + line, line, line[1:] + [None]):
            # check if variable is over
            if current_variable is not None:
                if current_variable == '' and self.is_id_first_char(char)\
                        or self.is_id_char(char):
                    new_line += char
                else:
                    if current_variable == '':
                        new_line += '$'
                    else:
                        new_line += self.dict[current_variable]
                    current_variable = None

            # check if variable starts
            if char == '$':
                if state == self.QuoteState.INSIDE_SINGLE:
                    new_line += char
                else:
                    current_variable = ''
                continue

            new_line += char

            if char == '\'':
                if state == self.QuoteState.OUTSIDE_QUOTES:
                    if prev_char != self.ESCAPE_CHARACTER:
                        state = self.QuoteState.INSIDE_SINGLE
                elif state == self.QuoteState.INSIDE_SINGLE:
                    if prev_char != self.ESCAPE_CHARACTER:
                        state = self.QuoteState.OUTSIDE_QUOTES
                elif state == self.QuoteState.INSIDE_DOUBLE:
                    pass
            elif char == '"':
                if state == self.QuoteState.OUTSIDE_QUOTES:
                    if prev_char != self.ESCAPE_CHARACTER:
                        state = self.QuoteState.INSIDE_DOUBLE
                elif state == self.QuoteState.INSIDE_SINGLE:
                    pass
                elif state == self.QuoteState.INSIDE_DOUBLE:
                    if prev_char != self.ESCAPE_CHARACTER:
                        state = self.QuoteState.OUTSIDE_QUOTES

        return new_line

    def tokenize(self, line):
        pass

    def parse(self, line):
        return []

    def interpret(self, line):
        line = self.expand(line)
        command = self.parse(line)
        command.run()
        print(line)





def main():
    interpreter = Interpreter()
    line = input('> ')
    while line:
        line = input('> ')
        interpreter.interpret(line)


if __name__ == '__main__':
    main()
