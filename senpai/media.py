from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional


def _clean_string(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    return cleaned or None


def is_http_url(value: Any) -> bool:
    cleaned = _clean_string(value)
    if not cleaned:
        return False
    return cleaned.lower().startswith(("http://", "https://"))


def get_character_image_url(character: Mapping[str, Any]) -> Optional[str]:
    if not isinstance(character, Mapping):
        return None

    value = character.get("img_url")
    if is_http_url(value):
        return value.strip()
    return None


def get_character_file_id(character: Mapping[str, Any]) -> Optional[str]:
    if not isinstance(character, Mapping):
        return None

    return _clean_string(character.get("tg_file_id"))


def get_character_media_reference(character: Mapping[str, Any]) -> Optional[str]:
    if not isinstance(character, Mapping):
        return None

    return get_character_image_url(character) or get_character_file_id(character)


def copy_character_media_fields(
    source: Mapping[str, Any],
    target: Optional[MutableMapping[str, Any]] = None,
) -> MutableMapping[str, Any]:
    media_target = dict(target or {})

    img_url = get_character_image_url(source)
    tg_file_id = get_character_file_id(source)

    media_target["img_url"] = img_url or ""
    if tg_file_id:
        media_target["tg_file_id"] = tg_file_id
    elif "tg_file_id" in media_target:
        media_target.pop("tg_file_id", None)

    return media_target
