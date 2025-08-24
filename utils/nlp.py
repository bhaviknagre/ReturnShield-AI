def text_consistency_score(reason: str, order_info: dict):
    text = reason.lower().strip()
    score = 0.2 if len(text) < 20 else 0.5
    if any(w in text for w in ["defect", "damaged", "rip", "broken", "stain", "scratch"]):
        score += 0.2
    if "size" in text and not order_info.get("size"):
        score -= 0.2
    if "color" in text and not order_info.get("color"):
        score -= 0.2
    return float(max(0.0, min(score, 1.0)))
