# (c) @SenpaiLabs
# SenpaiLabs Developer

from html import escape
from typing import Optional, Tuple

from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from senpai import LOGGER, application, user_collection
from senpai.security import ROLE_DEV, ROLE_OWNER, has_any_role, is_owner
from senpai.utils import to_small_caps


async def _is_allowed(user_id: int) -> bool:
    return await has_any_role(user_id, ROLE_OWNER, ROLE_DEV)


async def _resolve_target(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    if update.message and update.message.reply_to_message and update.message.reply_to_message.from_user:
        user = update.message.reply_to_message.from_user
        return user.id, user.first_name, None

    if not context.args:
        return None, None, "Reply to a user or pass a numeric user ID."

    raw_target = context.args[0].strip()
    if not raw_target.lstrip("-").isdigit():
        return None, None, "Target must be a numeric user ID."

    target_id = int(raw_target)
    if target_id <= 0:
        return None, None, "Target must be a valid user ID."

    target_name = None
    target_doc = await user_collection.find_one({"id": target_id}, {"first_name": 1})
    if target_doc:
        target_name = target_doc.get("first_name")

    return target_id, target_name, None


def _format_target(target_id: int, target_name: Optional[str]) -> str:
    if target_name:
        return f"{escape(target_name)} (<code>{target_id}</code>)"
    return f"<code>{target_id}</code>"


def _can_target(actor_id: int, target_id: int) -> bool:
    if is_owner(target_id) and not is_owner(actor_id):
        return False
    return True


async def ckill_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    actor_id = update.effective_user.id

    if not await _is_allowed(actor_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only developers or the owner can use this command.")
        )
        return

    target_id, target_name, error = await _resolve_target(update, context)
    if error:
        await update.message.reply_text(
            f"ℹ️ {to_small_caps(error)}\n"
            f"{to_small_caps('Usage')}: <code>/ckill &lt;user_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    if not _can_target(actor_id, target_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only the owner can clear the owner's balance.")
        )
        return

    previous_doc = await user_collection.find_one_and_update(
        {"id": target_id},
        {"$set": {"balance": 0}},
        projection={"balance": 1, "first_name": 1, "_id": 0},
        return_document=ReturnDocument.BEFORE,
    )

    if not previous_doc:
        await update.message.reply_text(
            "❌ " + to_small_caps("No saved user data was found for that ID.")
        )
        return

    previous_balance = int(previous_doc.get("balance", 0) or 0)
    if not target_name:
        target_name = previous_doc.get("first_name")

    LOGGER.debug(
        "Balance cleared by %s for target %s (previous balance=%s)",
        actor_id,
        target_id,
        previous_balance,
    )

    await update.message.reply_text(
        (
            f"<b>✅ {to_small_caps('Balance Cleared')}</b>\n\n"
            f"👤 <b>{to_small_caps('Target')}:</b> {_format_target(target_id, target_name)}\n"
            f"💰 <b>{to_small_caps('Previous Balance')}:</b> <code>{previous_balance:,}</code>\n"
            f"🧹 <b>{to_small_caps('New Balance')}:</b> <code>0</code>"
        ),
        parse_mode="HTML",
    )


async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    actor_id = update.effective_user.id

    if not await _is_allowed(actor_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only developers or the owner can use this command.")
        )
        return

    target_id, target_name, error = await _resolve_target(update, context)
    if error:
        await update.message.reply_text(
            f"ℹ️ {to_small_caps(error)}\n"
            f"{to_small_caps('Usage')}: <code>/kill &lt;user_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    if not _can_target(actor_id, target_id):
        await update.message.reply_text(
            "❌ " + to_small_caps("Only the owner can clear the owner's collection.")
        )
        return

    previous_doc = await user_collection.find_one_and_update(
        {"id": target_id},
        {"$set": {"characters": [], "favorites": []}},
        projection={"characters": 1, "favorites": 1, "first_name": 1, "_id": 0},
        return_document=ReturnDocument.BEFORE,
    )

    if not previous_doc:
        await update.message.reply_text(
            "❌ " + to_small_caps("No saved user data was found for that ID.")
        )
        return

    removed_characters = len(previous_doc.get("characters", []) or [])
    removed_favorites = len(previous_doc.get("favorites", []) or [])
    if not target_name:
        target_name = previous_doc.get("first_name")

    LOGGER.debug(
        "Collection cleared by %s for target %s (characters=%s, favorites=%s)",
        actor_id,
        target_id,
        removed_characters,
        removed_favorites,
    )

    await update.message.reply_text(
        (
            f"<b>✅ {to_small_caps('Collection Cleared')}</b>\n\n"
            f"👤 <b>{to_small_caps('Target')}:</b> {_format_target(target_id, target_name)}\n"
            f"🎴 <b>{to_small_caps('Characters Removed')}:</b> <code>{removed_characters}</code>\n"
            f"⭐ <b>{to_small_caps('Favorites Cleared')}:</b> <code>{removed_favorites}</code>"
        ),
        parse_mode="HTML",
    )


application.add_handler(CommandHandler("ckill", ckill_command, block=False))
application.add_handler(CommandHandler("kill", kill_command, block=False))
