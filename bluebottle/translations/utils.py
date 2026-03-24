import logging
import time

import requests
from django.conf import settings

from bluebottle.translations.models import Translation

logger = logging.getLogger('bluebottle')


class TranslationError(Exception):
    pass


def get_translation_response(text, target_language):
    url = settings.DEEPL_API_URL
    params = {
        "auth_key": settings.DEEPL_API_KEY,
        "text": text,
        "target_lang": target_language.upper(),
    }

    for attempt in range(3):
        resp = requests.post(url, data=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()["translations"][0]
            detected_source = data["detected_source_language"]
            if detected_source == target_language.upper():
                translated = {
                    'value': text,
                    'source_language': detected_source
                }
            else:
                translated = {
                    'value': data["text"],
                    'source_language': detected_source
                }
            return translated

        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(1.5 * (attempt + 1))
            continue
        logger.debug(f"DeepL error {resp.status_code}: {resp.text[:200]}")

        return {
            "value": text,
            "source_language": '??',
        }
    logger.debug("DeepL: retried and failed.")
    return {
        "value": text,
        "source_language": '??',
    }


def translate_text_cached(text, target_language):
    if not text:
        return None

    trans = Translation.objects.filter(
        text=text,
        target_language=target_language
    ).first()
    if trans:
        return {
            "value": trans.translation,
            "source_language": trans.source_language,
        }

    try:
        translated = get_translation_response(text, target_language)

        Translation.objects.create(
            target_language=target_language,
            source_language=translated["source_language"],
            text=text,
            translation=translated["value"],
        )
        return translated
    except Exception:
        return None
