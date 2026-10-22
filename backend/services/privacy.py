from __future__ import annotations
import re
import io
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Aadhaar pattern (12 digits, optional spaces or hyphens)
AADHAAR_REGEX = re.compile(r'\b(\d{4})[\s\-](\d{4})[\s\-](\d{4})\b')
AADHAAR_NOSPACE_REGEX = re.compile(r'\b(\d{12})\b')

def mask_aadhaar_string(text: Optional[str]) -> Optional[str]:
    """
    Masks any 12-digit Aadhaar pattern to XXXX-XXXX-Last4
    """
    if not text:
        return text
    
    def _repl(match):
        last4 = match.group(3) if match.lastindex >= 3 else match.group(0)[-4:]
        return f"XXXX-XXXX-{last4}"

    masked = AADHAAR_REGEX.sub(r'XXXX-XXXX-\3', text)
    masked = AADHAAR_NOSPACE_REGEX.sub(lambda m: f"XXXX-XXXX-{m.group(1)[-4:]}", masked)
    return masked

def mask_name_privacy(name: Optional[str]) -> Optional[str]:
    """
    Partially masks name for privacy-preserving summary QR (e.g., S******* RAKESH).
    """
    if not name:
        return name
    parts = name.strip().split()
    if len(parts) == 1:
        part = parts[0]
        if len(part) <= 2:
            return part
        return part[0] + "*" * (len(part) - 2) + part[-1]
    
    # Mask the first token, keep last token
    first = parts[0]
    masked_first = first[0] + "*" * max(1, len(first) - 1)
    return f"{masked_first} {' '.join(parts[1:])}"

def redact_image_region(
    image_bytes: bytes,
    box: Optional[Tuple[int, int, int, int]] = None,
    label: str = "[Aadhaar Redacted]"
) -> bytes:
    """
    In-memory overlay of a solid black banner with white text over the specified box.
    If no box is provided, draws a synthetic privacy badge across bottom-center.
    Never writes to disk.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    if box:
        x0, y0, x1, y1 = box
    else:
        # Default redaction area: bottom third centered band
        x0 = int(width * 0.20)
        y0 = int(height * 0.70)
        x1 = int(width * 0.80)
        y1 = int(height * 0.82)

    # Draw solid black rectangle
    draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0), outline=(220, 38, 38), width=2)
    
    # Draw label text
    font_size = max(12, int((y1 - y0) * 0.45))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    text_pos = (x0 + 10, y0 + max(2, (y1 - y0 - font_size) // 2))
    draw.text(text_pos, label, fill=(255, 255, 255), font=font)

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue()
