"""unmanaged_resource: flag a handle nothing in sight releases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "write_audit_log": 1,     # `Path(...).open()` is still an open file
    "read_payload": 1,        # annotated assignment
    "read_fallback": 1,       # walrus
    "load_config": 1,                   # opened, read, dropped
    "merge_parts": 2,                   # two acquisitions, one report each
    "fetch_rows": 1,                    # a cursor the card names as an acquisition
    "make_appender.append": 1,          # the closure that opens owns the finding
    "append_audit": 1,                  # the `with` reads a name off it, does not adopt it
    "IndexBuilder.read_manifest": 1,    # the attribute holds parsed data, not the handle
}


def test_unmanaged_resource():
    check("unmanaged_resource", CASES, EXPECTED)


if __name__ == "__main__":
    test_unmanaged_resource()
    print("ok")
