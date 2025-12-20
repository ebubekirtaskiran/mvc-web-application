# file_generator.py  — Proje köküne sabitlenen sürüm
import os
from pathlib import Path

# --- Ayar ---
hedef_klasor = "indirilenler"   # "masaustu" / "indirilenler" / "resimler" vb.

olusturulacak_dosya_sayisi = 1000
dosya_temel_adi = "rapor"
dosya_uzantisi = ".txt"

# --- Yol çözümü: proje kökünü betiğin konumuna sabitle ---
PROJE_KOK = Path(__file__).resolve().parent           # Ebu-Final/
TARGET_DIR = (PROJE_KOK / hedef_klasor).resolve()     # Ebu-Final/indirilenler (veya masaustu)

# Güvenlik: hedef mutlaka proje kökü altında olsun
try:
    # Python 3.9+: is_relative_to var
    if not TARGET_DIR.is_relative_to(PROJE_KOK):
        raise ValueError(f"Hedef proje kökü dışında: {TARGET_DIR}")
except AttributeError:
    # Daha eski sürümlerde alternatif kontrol
    if PROJE_KOK not in TARGET_DIR.parents and TARGET_DIR != PROJE_KOK:
        raise ValueError(f"Hedef proje kökü dışında: {TARGET_DIR}")

# Hedef klasör yoksa oluştur (istersen kapatabilirsin)
TARGET_DIR.mkdir(parents=True, exist_ok=True)

print(f"Yazılacak yer: {TARGET_DIR}")

# --- Dosya üretimi ---
for i in range(olusturulacak_dosya_sayisi):
    dosya_adi = f"{dosya_temel_adi}_{i+1}{dosya_uzantisi}"
    dosya_yolu = TARGET_DIR / dosya_adi
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        f.write(f"Bu, {i+1}. dosyadır.\n")
print(f"Başarıyla {olusturulacak_dosya_sayisi} dosya oluşturuldu -> {TARGET_DIR}")
