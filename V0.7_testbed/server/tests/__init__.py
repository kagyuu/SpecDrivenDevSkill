"""テストパッケージ。`server/src` を import パスに追加する。

`cd server && python3 -m unittest discover -s tests -t .` および
`cd server && python3 -m unittest tests.integration.test_t0NN_xxx` の双方で
`meeting_room` パッケージを解決できるようにするための最小の初期化。
"""

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
