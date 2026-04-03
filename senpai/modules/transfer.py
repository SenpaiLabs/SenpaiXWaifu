# (c) @SenpaiLabs
# SenpaiLabs Developer

from html import escape
from typing import Optional

from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from senpai import LOGGER, application, user_collection
from senpai.character_ids import normalize_character_document
from senpai.security import ROLE_DEV, ROLE_OWNER, has_any_role, is_owner
from senpai.utils import to_small_caps


async def _is_allowed(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV)


def _format_user_label(user_id: int, first_name: Optional[str]) -> str:
    if first_name:
        return f"{escape(first_name)} (<code>{user_id}</code>)"
    return f"<code>{user_id}</code>"


def _can_touch_target(actor_id: int, target_id: int) -> bool:
    if is_owner(target_id) and not is_owner(actor_id):
        return False
    return True


async def transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    actor_id = update.effective_user.id

    if not await _is_allowed(actor_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only developers or the owner can use this command.")
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            (
                f"ℹ️ {to_small_caps('Usage')}: <code>/transfer &lt;source_user_id&gt; &lt;target_user_id&gt;</code>\n"
                f"💡 {to_small_caps('Example')}: <code>/transfer 12345 67890</code>"
            ),
            parse_mode="HTML",
        )
        return

    raw_source_id = context.args[0].strip()
    raw_target_id = context.args[1].strip()
    if not raw_source_id.lstrip("-").isdigit() or not raw_target_id.lstrip("-").isdigit():
        await update.message.reply_text(
            "❌ " + to_small_caps("Both source and target must be numeric user IDs.")
        )
        return

    source_id = int(raw_source_id)
    target_id = int(raw_target_id)
    if source_id <= 0 or target_id <= 0:
        await update.message.reply_text(
            "❌ " + to_small_caps("Both source and target must be valid user IDs.")
        )
        return

    if source_id == target_id:
        await update.message.reply_text(
            "❌ " + to_small_caps("Source and target IDs cannot be the same.")
        )
        return

    if not _can_touch_target(actor_id, source_id) or not _can_touch_target(actor_id, target_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only the owner can transfer collections involving the owner account.")
        )
        return

    source_preview = await user_collection.find_one(
        {"id": source_id},
        {"characters": 1, "favorites": 1, "first_name": 1, "_id": 0},
    )
    if not source_preview:
        await update.message.reply_text(
            "❌ " + to_small_caps("Source user data was not found.")
        )
        return

    preview_characters = source_preview.get("characters", []) or []
    if not preview_characters:
        await update.message.reply_text(
            "❌ " + to_small_caps("Source user has no collection to transfer.")
        )
        return

    source_doc = await user_collection.find_one_and_update(
        {"id": source_id},
        {"$set": {"characters": [], "favorites": []}},
        projection={"characters": 1, "favorites": 1, "first_name": 1, "_id": 0},
        return_document=ReturnDocument.BEFORE,
    )
    if not source_doc:
        await update.message.reply_text(
            "❌ " + to_small_caps("Source user data was not found.")
        )
        return

    source_characters = [
        normalize_character_document(character)
        for character in (source_doc.get("characters", []) or [])
    ]
    if not source_characters:
        await update.message.reply_text(
            "❌ " + to_small_caps("Source user has no collection to transfer.")
        )
        return

    source_favorites = source_doc.get("favorites", []) or []
    source_name = source_doc.get("first_name")
    target_doc = await user_collection.find_one({"id": target_id}, {"first_name": 1, "_id": 0})
    target_name = target_doc.get("first_name") if target_doc else None

    try:
        await user_collection.update_one(
            {"id": target_id},
            {
                "$push": {"characters": {"$each": source_characters}},
                "$setOnInsert": {
                    "id": target_id,
                    "balance": 0,
                    "characters": [],
                    "favorites": [],
                },
            },
            upsert=True,
        )
    except Exception as exc:
        LOGGER.exception(
            "Transfer failed while pushing source %s collection to target %s",
            source_id,
            target_id,
        )
        try:
            await user_collection.update_one(
                {"id": source_id},
                {
                    "$push": {"characters": {"$each": source_characters}},
                    "$set": {"favorites": source_favorites},
                    "$setOnInsert": {
                        "id": source_id,
                        "balance": 0,
                        "characters": [],
                        "favorites": [],
                    },
                },
                upsert=True,
            )
        except Exception:
            LOGGER.exception(
                "Rollback failed after transfer error for source %s -> target %s",
                source_id,
                target_id,
            )
        await update.message.reply_text(
            "❌ " + to_small_caps("Transfer failed. The move was rolled back if possible. Please try again later.")
        )
        return

    LOGGER.debug(
        "Collection transferred by %s from source %s to target %s (characters=%s)",
        actor_id,
        source_id,
        target_id,
        len(source_characters),
    )

    await update.message.reply_text(
        (
            f"<b>✅ {to_small_caps('Collection Transferred')}</b>\n\n"
            f"📤 <b>{to_small_caps('From')}:</b> {_format_user_label(source_id, source_name)}\n"
            f"📥 <b>{to_small_caps('To')}:</b> {_format_user_label(target_id, target_name)}\n"
            f"🎴 <b>{to_small_caps('Characters Moved')}:</b> <code>{len(source_characters)}</code>\n"
            f"⭐ <b>{to_small_caps('Source Favorites Cleared')}:</b> <code>{len(source_favorites)}</code>"
        ),
        parse_mode="HTML",
    )


application.add_handler(CommandHandler("transfer", transfer_command, block=False))
