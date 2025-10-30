import hashlib, time, requests
from django.conf import settings
from django.core.cache import cache

class TranslationError(Exception): pass

def _cache_key(text, target_lang, provider="deepl"):
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"tr:{provider}:{target_lang.upper()}:{h}"

def translate_text_cached(text, target_lang):
    if not text:
        return ""
    key = _cache_key(text, target_lang, "deepl")
    cached = cache.get(key)
    if cached is not None:
        return cached

    url = settings.DEEPL_API_URL
    params = {
        "auth_key": settings.DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang.upper(),
    }

    for attempt in range(3):
        resp = requests.post(url, data=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()["translations"][0]
            detected_source = data["detected_source_language"]
            if detected_source == target_lang.upper():
                translated = {
                    'value': text,
                    'source_language': detected_source
                }
            else:
                translated = {
                    'value': data["text"],
                    'source_language': detected_source
                }
            cache.set(key, translated, 60 * 60 * 24 * 1000)
            return translated

        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(1.5 * (attempt + 1))
            continue
        raise TranslationError(f"DeepL error {resp.status_code}: {resp.text[:200]}")
    raise TranslationError("DeepL: retried and failed.")
