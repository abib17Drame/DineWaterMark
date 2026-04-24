"""
Suppression du watermark visible Gemini par inversion mathematique
(alpha compositing reverse).

Formule directe:
  watermarked = alpha * 255 + (1 - alpha) * original

Inversion:
  original = (watermarked - alpha * 255) / (1 - alpha)
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

LOGO_VALUE = 255.0
ALPHA_THRESHOLD = 0.002
MAX_ALPHA = 0.99

ASSETS_DIR = Path(__file__).parent / "templates"
CONFIGS = {
    "small": ("bg_48.png", 48, 32),
    "large": ("bg_96.png", 96, 64),
}

_alpha_cache: dict[str, np.ndarray] = {}


def _pick_variant(width: int, height: int) -> str:
    if width > 1024 and height > 1024:
        return "large"
    return "small"


def _watermark_box(width: int, height: int, variant: str) -> tuple[int, int, int, int]:
    _, logo_size, margin = CONFIGS[variant]
    x1 = width - margin - logo_size
    y1 = height - margin - logo_size
    x2 = x1 + logo_size
    y2 = y1 + logo_size
    return x1, y1, x2, y2


def _load_alpha_map(variant: str) -> np.ndarray:
    if variant in _alpha_cache:
        return _alpha_cache[variant]

    filename = CONFIGS[variant][0]
    path = ASSETS_DIR / filename
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Alpha map introuvable: {path}")

    alpha = np.max(img, axis=2).astype(np.float64) / 255.0
    alpha = np.clip(alpha, 0.0, MAX_ALPHA)
    alpha[alpha < ALPHA_THRESHOLD] = 0.0

    _alpha_cache[variant] = alpha
    return alpha


def supprimer_watermark_gemini_math(image: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    Supprime le logo Gemini visible via inversion mathematique.

    Retourne (image_nettoyee, infos).
    """
    img = image.copy()
    h, w = img.shape[:2]

    variant = _pick_variant(w, h)
    alpha = _load_alpha_map(variant)
    x1, y1, x2, y2 = _watermark_box(w, h, variant)

    # Clamp a l'image
    rx1 = max(x1, 0)
    ry1 = max(y1, 0)
    rx2 = min(x2, w)
    ry2 = min(y2, h)

    ax1 = rx1 - x1
    ay1 = ry1 - y1
    ax2 = ax1 + (rx2 - rx1)
    ay2 = ay1 + (ry2 - ry1)

    region = img[ry1:ry2, rx1:rx2].astype(np.float64)
    a = alpha[ay1:ay2, ax1:ax2]
    a3 = np.stack([a, a, a], axis=-1)

    mask = a3 > ALPHA_THRESHOLD
    restored = region.copy()
    denom = 1.0 - a3
    restored[mask] = (region[mask] - a3[mask] * LOGO_VALUE) / denom[mask]
    restored = np.clip(restored, 0, 255).astype(np.uint8)

    result = img.copy()
    result[ry1:ry2, rx1:rx2] = restored

    info = {
        "watermark_detecte": True,
        "watermark_source": "gemini",
        "methode": "gemini_reverse_alpha",
        "position": {
            "x": int(rx1),
            "y": int(ry1),
            "largeur": int(rx2 - rx1),
            "hauteur": int(ry2 - ry1),
        },
        "variant": variant,
        "pixels_corriges": int(np.count_nonzero(mask)),
    }

    return result, info
 