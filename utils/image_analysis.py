from PIL import Image, ImageStat, ImageFilter, ExifTags
import numpy as np
import os

def ahash(img, hash_size=8):
    # Average hash (aHash)
    img = img.convert("L").resize((hash_size, hash_size), Image.BILINEAR)
    pixels = np.array(img)
    avg = pixels.mean()
    diff = pixels > avg
    return diff

def hamming(a, b):
    return np.count_nonzero(a != b)

def image_similarity(upload_path, ref_path):
    if not (os.path.exists(upload_path) and os.path.exists(ref_path)):
        return 0.0
    img1 = Image.open(upload_path).convert("RGB")
    img2 = Image.open(ref_path).convert("RGB")
    h1 = ahash(img1)
    h2 = ahash(img2)
    dist = hamming(h1, h2)
    max_bits = h1.size
    sim = 1.0 - (dist / max_bits)
    return float(sim)

def brightness_score(upload_path):
    img = Image.open(upload_path).convert("L")
    stat = ImageStat.Stat(img)
    # Normalize to 0..1 using typical 8-bit range
    return float(stat.mean[0] / 255.0)

def blur_score(upload_path):
    img = Image.open(upload_path).convert("L")
    # Use variance of Laplacian via built-in filter approximation
    lap = img.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(lap)
    # Higher variance -> sharper; we'll normalize crudely
    var = np.var(np.array(lap))
    # Map to 0..1 using heuristic cap
    return float(min(var / 5000.0, 1.0))

def exif_metadata_score(upload_path):
    try:
        img = Image.open(upload_path)
        exif = img.getexif()
        if not exif:
            return 0.3  # missing metadata slightly suspicious
        # Presence of common tags boosts score
        keys = [ExifTags.TAGS.get(k, str(k)) for k in exif.keys()]
        score = 0.3
        for tag in ["DateTime", "Model", "Make"]:
            if tag in keys:
                score += 0.2
        return float(min(score, 1.0))
    except Exception:
        return 0.3
