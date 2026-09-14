import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import bind  # noqa: E402
CHECK, RUBRIC, Invalid, _parse_dir, validate = bind(HERE)
