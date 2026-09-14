"""Apply an exact reversible EDKit transform."""
import json
from pathlib import Path
import sys
spec, root = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
for edit in json.loads(spec.read_text())["edits"]:
    path = root / edit["file"]
    assert path.resolve().is_relative_to(root) and not path.is_symlink()
    raw = path.read_bytes()
    old, new = edit["old"].encode(), edit["new"].encode()
    assert raw.count(old) == 1, "edit must occur exactly once"
    path.write_bytes(raw.replace(old, new, 1))
