from typing import List, Dict


PLATFORM_ALIASES: Dict[str, str] = {
    "fb": "facebook",
    "facebook": "facebook",
    "ig": "instagram",
    "instagram": "instagram",
    "li": "linkedin",
    "linkedin": "linkedin",
}


def normalize_platforms(platforms: List[str]) -> List[str]:
    norm: List[str] = []
    for p in platforms:
        key = p.strip().lower()
        if key in PLATFORM_ALIASES:
            value = PLATFORM_ALIASES[key]
            if value not in norm:
                norm.append(value)
    return norm


def classify_platforms(payload: Dict) -> List[str]:
    """
    Heuristic classifier for target platforms.

    Priority:
    - Use explicit `platforms` or `platform` in payload if present
    - Else infer based on content keywords
    - Fallback to all supported (facebook, instagram, linkedin)
    """
    # Explicit platforms
    if "platforms" in payload and isinstance(payload["platforms"], list):
        norm = normalize_platforms([str(p) for p in payload["platforms"]])
        if norm:
            return norm

    if "platform" in payload and isinstance(payload["platform"], str):
        norm = normalize_platforms([payload["platform"]])
        if norm:
            return norm

    # Heuristic from content
    content = (payload.get("content") or payload.get("caption") or "").lower()
    topic = (payload.get("topic") or "").lower()
    text = f"{topic} {content}"

    inferred: List[str] = []
    # Instagram: hashtags, emojis, aesthetic terms
    if any(tok in text for tok in ["#", "📸", "inspo", "before and after", "aesthetic"]):
        inferred.append("instagram")
    # LinkedIn: professional terms
    if any(tok in text for tok in ["b2b", "case study", "insights", "whitepaper", "professional", "industry"]):
        inferred.append("linkedin")
    # Facebook: general consumer tone or community mentions
    if any(tok in text for tok in ["community", "family", "local", "special", "deal", "news"]):
        inferred.append("facebook")

    if inferred:
        # Deduplicate and preserve order preference
        out: List[str] = []
        for p in ["facebook", "instagram", "linkedin"]:
            if p in inferred and p not in out:
                out.append(p)
        return out

    # Fallback
    return ["facebook", "instagram", "linkedin"]

