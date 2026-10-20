"""End-to-end CLI behavior on a small local package."""

import contextlib
import io
import json
import struct
import tempfile
import unittest
from pathlib import Path

from ps5fwlab.__main__ import main


class CLITests(unittest.TestCase):
    def test_inspect_and_entropy_emit_machine_readable_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pup"
            data = bytearray(1024)
            struct.pack_into("<4s7I", data, 0, b"SLB2", 3, 0, 1, 2, 0, 0, 0)
            struct.pack_into("<4I32s", data, 0x20, 1, 256, 0, 0, b"PART.PUP")
            data[512:768] = bytes(range(256))
            path.write_bytes(data)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["inspect", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["entries"][0]["offset"], 512)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["entropy", str(path), "--window", "256", "--samples", "1"])
            self.assertEqual(code, 0)
            self.assertAlmostEqual(json.loads(output.getvalue())["entries"][0]["samples"][0]["entropy_bits_per_byte"], 8.0)


if __name__ == "__main__":
    unittest.main()
