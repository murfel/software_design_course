import abc
import os


class RunnableCommand(abc.ABC):
    def __init__(self, args, stdin):
        self.args = args
        self.stdin = stdin

    @abc.abstractmethod
    def run(self):
        pass


class EchoCommand(RunnableCommand):
    def run(self):
        return ' '.join(self.args)


class CatCommand(RunnableCommand):
    def run(self):
        with open(self.args[0]) as file:
            return file.read()


class WcCommand(RunnableCommand):
    def run(self):
        with open(self.args[0]) as file:
            content = file.read()
            num_lines = content.count('\n')
            num_words = len(content.split())
            num_bytes = len(content.encode())
            return f'{num_lines} {num_words} {num_bytes}'


class PwdCommand(RunnableCommand):
    def run(self):
        return os.getcwd()