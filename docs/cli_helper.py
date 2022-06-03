# Generate CLI page
# Needs imports, so run with full

import pydrobert.kaldi.command_line as cli
import os
from io import StringIO
import sys
import inspect
import warnings

warnings.simplefilter("ignore")

# Modified from
# https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = sys.stderr = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout
        sys.stderr = self._stderr


DIR = os.path.dirname(__file__)
CLI_RST = os.path.join(DIR, "source", "cli.rst")

buff = "Command-Line Interface\n======================\n\n"
for cmd_name in (
    "write-table-to-pickle",
    "write-pickle-to-table",
    "compute-error-rate",
    "normalize-feat-lens",
    "write-table-to-torch-dir",
    "write-torch-dir-to-table",
):
    buff += cmd_name + "\n" + ("-" * len(cmd_name)) + "\n\n::\n\n  "
    sys.argv[0] = cmd_name
    func = next(
        x[1] for x in inspect.getmembers(cli) if x[0] == cmd_name.replace("-", "_")
    )
    with Capturing() as c:
        try:
            func(["-h"])
        except SystemExit:
            pass
    buff += "\n  ".join(c) + "\n\n"

with open(CLI_RST, "w") as f:
    f.write(buff)
