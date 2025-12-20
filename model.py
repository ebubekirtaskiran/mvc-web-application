import os
from pathlib import Path
from typing import Callable, List, Optional


BASE_DIR = Path(__file__).parent

# === OBSERVER: watchdog ile dizin değişimi izleme ===
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object


class _FsHandler(FileSystemEventHandler):
    """Dosya sistemi olaylarını yakalayıp abonelere haber veren handler."""
    def __init__(self, notify: Callable[[dict], None]):
        super().__init__()
        self._notify = notify

    def on_any_event(self, event):
        # sadece dosya/klasör değişimlerini bildir (temp/py dosyalarını filtreleyebiliriz)
        src = getattr(event, "src_path", "")
        name = os.path.basename(src)

        # Gizli dosyalar ve .py dosyalarını izleme raporundan çıkar
        if name.startswith(".") or name.endswith(".py"):
            return

        payload = {
            "event_type": getattr(event, "event_type", "unknown"),
            "is_directory": bool(getattr(event, "is_directory", False)),
            "path": src,
        }
        self._notify(payload)


class DirectoryObserver:
    """
    Observer deseni:
    - Model: dosya sistemi değişimini izler (watchdog)
    - Observers: controller tarafında subscribe olan callbackler
    """
    def __init__(self, base_dir: Path, watch_folders: List[str]):
        if Observer is None:
            raise RuntimeError("watchdog kurulu değil. Kur: pip install watchdog")

        self.base_dir = base_dir
        self.watch_folders = watch_folders
        self._subscribers: List[Callable[[dict], None]] = []

        self._observer = None

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        """Observer ekle (Controller bu callback’i verir)."""
        self._subscribers.append(callback)

    def _notify_all(self, payload: dict) -> None:
        for cb in list(self._subscribers):
            try:
                cb(payload)
            except Exception:
                # bir subscriber patlarsa diğerlerini etkilemesin
                pass

    def start(self) -> None:
        """İzlemeyi başlat."""
        if self._observer is not None:
            return  # zaten çalışıyor

        handler = _FsHandler(self._notify_all)
        obs = Observer()

        # Sadece belirlediğimiz klasörleri izle
        for folder in self.watch_folders:
            p = (self.base_dir / folder)
            p.mkdir(parents=True, exist_ok=True)
            obs.schedule(handler, str(p), recursive=True)

        obs.daemon = True
        obs.start()
        self._observer = obs

    def stop(self) -> None:
        """İzlemeyi durdur."""
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=2)
        self._observer = None


# === Mevcut fonksiyonun (listeleme) — aynen korunuyor ===
def list_items(directory_name: str):
    """
    Belirtilen klasördeki dosya ve klasörleri listeler.
    Güvenlik: '..' içermemeli ve sadece BASE_DIR altında olmalı.
    """
    if ".." in directory_name:
        return {"error": "Geçersiz yol."}

    try:
        target_path_str = os.path.normpath(directory_name)
        target_dir = BASE_DIR / target_path_str

        # Python 3.9+ için resolve + relative kontrol
        if not target_dir.resolve().is_relative_to(BASE_DIR.resolve()):
            return {"error": "Erişim engellendi."}

        if not target_dir.is_dir():
            return {"error": f"'{directory_name}' klasörü bulunamadı."}

    except Exception:
        return {"error": "Geçersiz yol."}

    items = []
    try:
        for p in sorted(target_dir.iterdir()):
            if p.name.startswith('.') or p.name.endswith('.py'):
                continue

            items.append({
                "name": p.name + ("/" if p.is_dir() else ""),
                "is_folder": p.is_dir()
            })
        return items

    except PermissionError:
        return {"error": "Klasör okuma izni yok."}


def create_folder(path: str, new_folder_name: str):
    return {"status": "ok"}

def delete_item(path: str, item_name: str):
    return {"status": "ok"}

def rename_item(path: str, old_name: str, new_name: str):
    return {"status": "ok"}
