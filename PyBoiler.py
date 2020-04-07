import sys
import time
import os
import datetime

class Boilerplate:
    """Class meant for use by the subprocesses. Contains boilerplate functionality."""
    def __init__(self):
        self.name = sys.argv[0].split("\\")[-1].split(".")[0]
        self.module_path = "\\".join(sys.argv[0].split("\\")[:-1])
        self.args = sys.argv[1:]
    
    def read_from_larva(self) -> list:
        """Check if there are new inputs from Larva.

        Returns a list where each element is a command (line) from Larva."""
        return file_flush(pipe_path(self.name))

    def m_path(self, s: str) -> str:
        """Construct path to s in module."""
        return self.module_path + "\\" + s

class Log:
    def __init__(self, contents: str, use_timestamp=True):
        self.contents = str(contents)
        self.name = sys.argv[0].split("\\")[-1].split(".")[0]
        self.use_timestamp = use_timestamp

    def build(self) -> str:
        log = f"{timestamp()} " * self.use_timestamp
        log += f"{self.name}: {self.contents}"
        return log

    def to_larva(self, pipeline=True) -> None:
        """Display the log.
        
        Use the pipeline if `pipeline`, else print out the log."""
        if "-larva" in sys.argv and pipeline:
            file_write(pipe_path("larva"), self.build(), "a")
        else:
            print(self.build())

def tick(x: float) -> float:
    """Sleep for x seconds. Returns x."""
    time.sleep(x)
    return x

def file_read(path: str) -> str:
    """Wrapper function to read from a file in one line.
    
    Returns empty string if file doesn't exist."""
    if os.path.isfile(path):
        while True:
            try:
                with open(path, "r") as fptr:
                    return fptr.read()
            except PermissionError:
                pass
    return ""

def file_write(path: str, contents="", mode="w") -> None:
    """Wrapper function to write to a file in one line."""
    while True:
        try:
            with open(path, mode, encoding="utf-8") as fptr:
                fptr.write(f"{contents}\n")
                return None
        except PermissionError:
            pass

def file_flush(path: str) -> list:
    """Read from a file and return the contents as a list split by newlines, leaving the file empty afterwards.
    
    Returns empty list is file doesn't exist."""
    contents = file_read(path).strip()
    if not contents:
        return []
    file_write(path)
    return [line for line in contents.split("\n") if line]

def timestamp() -> str:
    """Returns a timestamp in the form of %H:%M:%S"""
    return f"[{datetime.datetime.now().strftime('%H:%M:%S')}]"

def pipe_path(name: str, extension=".txt") -> str:
    """Build a path to the filename in the pipeline folder."""
    return "\\".join(sys.argv[0].split("\\")[:-3]) + f"\\pipeline\\{name}{extension}"
