# view.py
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


def _read_file(path: Path) -> str:
    """Verilen dosyayı UTF-8 olarak okur ve döndürür."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_main_page() -> str:
    """Tek panel dosya gezgini (index.html)."""
    return _read_file(STATIC_DIR / "index.html")


def render_gateway_page() -> str:
    """4 panelli gateway (gateway.html)."""
    return _read_file(STATIC_DIR / "gateway.html")
