"""Generated from data/manual_sampling/NotCaching/Softmax2.

Do not edit: regenerate with `python validation/generate_sample_cases.py`.
The pair itself is the thing under test, so the case file must stay a faithful
transcription of it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sample import build  # noqa: E402

before, after, cases = build('NotCaching', 'Softmax2')
