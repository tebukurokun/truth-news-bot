"""ERROR 以上のログを ntfy にプッシュ通知するハンドラ.

`NTFY_URL`（例: https://ntfy.sh/<topic>）が未設定なら何もしない。
トピック名はそれ自体が合言葉なので、URL はコードに書かず production.env に置く。
"""

import os
import time
import urllib.request
from logging import ERROR, Handler, LogRecord
from threading import Lock

# 通知の失敗・遅延でボットを止めないための上限
SEND_TIMEOUT_SECONDS = 5

# 同じ種類のエラーを連続通知しないためのクールダウン（既定 30 分）。
# トークン失効時は記事ごとに Max retry exceeded が出るため、これが無いと通知が溢れる。
DEFAULT_COOLDOWN_SECONDS = 1800

# ntfy の本文上限に収まるよう切り詰める（traceback がそのまま入るため）
MAX_BODY_LENGTH = 1500


class NtfyHandler(Handler):
    """ERROR 以上のレコードを ntfy に POST する logging ハンドラ."""

    def __init__(self):
        super().__init__(level=ERROR)
        self._lock = Lock()
        self._last_sent: dict[str, float] = {}
        self._suppressed: dict[str, int] = {}

    def emit(self, record: LogRecord):
        try:
            # setup_logger は load_dotenv() より先に呼ばれることがあるので、
            # URL は import 時ではなく通知時に読む。
            url = os.getenv("NTFY_URL")
            if not url:
                return

            body = self._throttle(_error_kind(record), self.format(record))
            if body is None:
                return

            self._send(url, record.levelname, body)

        except Exception:  # pylint: disable=broad-except
            # 通知経路の失敗をボット本体に波及させない
            self.handleError(record)

    def _throttle(self, key: str, message: str) -> str | None:
        """クールダウン中なら None を返し、抑制した件数を次の通知に添える."""
        cooldown = int(os.getenv("NTFY_COOLDOWN_SECONDS", DEFAULT_COOLDOWN_SECONDS))
        now = time.monotonic()

        with self._lock:
            last_sent = self._last_sent.get(key)
            if last_sent is not None and now - last_sent < cooldown:
                self._suppressed[key] = self._suppressed.get(key, 0) + 1
                return None

            suppressed = self._suppressed.pop(key, 0)
            self._last_sent[key] = now

        if suppressed:
            message += f"\n(同種のエラー {suppressed} 件は通知を抑制しました)"

        return message[:MAX_BODY_LENGTH]

    def _send(self, url: str, level_name: str, body: str):
        request = urllib.request.Request(
            url,
            data=body.encode("utf-8"),
            headers={
                # ヘッダは ASCII のみ。日本語は本文側に入る。
                "Title": f"truth-bot {level_name}",
                "Priority": "high",
                "Tags": "rotating_light",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=SEND_TIMEOUT_SECONDS):
            pass


def _error_kind(record: LogRecord) -> str:
    """通知抑制のキー。記事名などの可変部分を落として種類だけを見る."""
    return record.getMessage().split(":")[0][:80]


# 定数ではなく遅延初期化のキャッシュなので UPPER_CASE にはしない
_handler: NtfyHandler | None = None  # pylint: disable=invalid-name
_handler_lock = Lock()


def get_ntfy_handler() -> NtfyHandler:
    """全 logger で共有するハンドラを返す（抑制状態をプロセス全体で共有するため）."""
    global _handler  # pylint: disable=global-statement

    with _handler_lock:
        if _handler is None:
            _handler = NtfyHandler()

        return _handler
