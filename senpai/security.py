# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from cachetools import TTLCache

from senpai.config import Config

ROLE_USER = "user"
ROLE_UPLOADER = "uploader"
ROLE_SUDO = "sudo"
ROLE_DEV = "dev"
ROLE_OWNER = "owner"

MANAGED_ROLES = (ROLE_UPLOADER, ROLE_SUDO, ROLE_DEV)

ROLE_LABELS = {
    ROLE_USER: "Normal User",
    ROLE_UPLOADER: "Uploader",
    ROLE_SUDO: "Sudo User",
    ROLE_DEV: "Developer",
    ROLE_OWNER: "Owner",
}

_role_cache: TTLCache[int, Optional[Dict[str, Any]]] = TTLCache(maxsize=5000, ttl=60)
_role_list_cache: TTLCache[str, List[Dict[str, Any]]] = TTLCache(maxsize=10, ttl=60)
_indexes_initialized = False


def is_owner(user_id: int) -> bool:
    return isinstance(user_id, int) and user_id == Config.OWNER_ID


def can_use_eval(user_id: int) -> bool:
    return is_owner(user_id)


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, "Unknown")


def _get_staff_collection():
    from senpai import db

    return db["staff_roles"]


async def _ensure_staff_indexes() -> None:
    global _indexes_initialized
    if _indexes_initialized:
        return

    collection = _get_staff_collection()
    try:
        await collection.create_index("user_id", unique=True)
    except Exception:
        pass

    try:
        await collection.create_index("role")
    except Exception:
        pass

    _indexes_initialized = True


def _clear_role_cache(user_id: Optional[int] = None) -> None:
    if user_id is None:
        _role_cache.clear()
    else:
        _role_cache.pop(user_id, None)
    _role_list_cache.clear()


async def get_staff_record(user_id: int) -> Optional[Dict[str, Any]]:
    if not isinstance(user_id, int) or is_owner(user_id):
        return None

    cached = _role_cache.get(user_id)
    if cached is not None or user_id in _role_cache:
        return cached

    await _ensure_staff_indexes()
    document = await _get_staff_collection().find_one({"user_id": user_id}, {"_id": 0})
    _role_cache[user_id] = document
    return document


async def get_user_role(user_id: int) -> str:
    if is_owner(user_id):
        return ROLE_OWNER

    document = await get_staff_record(user_id)
    if not document:
        return ROLE_USER

    role = document.get("role", ROLE_USER)
    return role if role in MANAGED_ROLES else ROLE_USER


async def has_any_role(user_id: int, *roles: str) -> bool:
    return await get_user_role(user_id) in roles


async def can_upload_characters(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO, ROLE_UPLOADER)


async def can_manage_upload_catalog(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO)


async def can_give_characters(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO)


async def can_generate_redeem_codes(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO)


async def can_manage_uploaders(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO)


async def can_manage_sudo(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV)


async def can_manage_dev(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER)


async def can_view_staff(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV, ROLE_SUDO, ROLE_UPLOADER)


async def upsert_staff_role(
    user_id: int,
    role: str,
    assigned_by: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> None:
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")
    if role not in MANAGED_ROLES:
        raise ValueError("Invalid staff role")
    if is_owner(user_id):
        raise ValueError("Owner role cannot be changed")

    await _ensure_staff_indexes()
    now = datetime.utcnow()
    await _get_staff_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "role": role,
                "username": username,
                "first_name": first_name,
                "assigned_by": assigned_by,
                "assigned_at": now,
                "updated_at": now,
            }
        },
        upsert=True,
    )
    _clear_role_cache(user_id)


async def remove_staff_role(user_id: int, expected_role: Optional[str] = None) -> bool:
    if not isinstance(user_id, int) or is_owner(user_id):
        return False

    await _ensure_staff_indexes()
    query: Dict[str, Any] = {"user_id": user_id}
    if expected_role:
        query["role"] = expected_role

    result = await _get_staff_collection().delete_one(query)
    if result.deleted_count:
        _clear_role_cache(user_id)
        return True
    return False


async def list_staff_members(role: str) -> List[Dict[str, Any]]:
    if role not in MANAGED_ROLES:
        return []

    cached = _role_list_cache.get(role)
    if cached is not None:
        return [dict(item) for item in cached]

    await _ensure_staff_indexes()
    documents = await _get_staff_collection().find({"role": role}, {"_id": 0}).to_list(length=None)
    documents.sort(
        key=lambda item: (
            str(item.get("first_name") or "").lower(),
            str(item.get("username") or "").lower(),
            int(item.get("user_id", 0)),
        )
    )
    _role_list_cache[role] = [dict(item) for item in documents]
    return documents


def format_staff_name(staff_doc: Dict[str, Any]) -> str:
    first_name = (staff_doc.get("first_name") or "").strip()
    username = (staff_doc.get("username") or "").strip()
    user_id = staff_doc.get("user_id", "Unknown")

    if first_name:
        return first_name
    if username:
        return f"@{username.lstrip('@')}"
    return str(user_id)


__all__ = [
    "ROLE_USER",
    "ROLE_UPLOADER",
    "ROLE_SUDO",
    "ROLE_DEV",
    "ROLE_OWNER",
    "MANAGED_ROLES",
    "role_label",
    "format_staff_name",
    "is_owner",
    "can_use_eval",
    "get_staff_record",
    "get_user_role",
    "has_any_role",
    "can_upload_characters",
    "can_manage_upload_catalog",
    "can_give_characters",
    "can_generate_redeem_codes",
    "can_manage_uploaders",
    "can_manage_sudo",
    "can_manage_dev",
    "can_view_staff",
    "upsert_staff_role",
    "remove_staff_role",
    "list_staff_members",
]

# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
