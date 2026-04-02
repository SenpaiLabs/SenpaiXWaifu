# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

from html import escape
from typing import Optional

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from senpai import application, LOGGER, pm_users, user_collection
from senpai.config import Config
from senpai.security import (
    ROLE_DEV,
    ROLE_SUDO,
    ROLE_UPLOADER,
    can_manage_dev,
    can_manage_sudo,
    can_manage_uploaders,
    can_view_staff,
    format_staff_name,
    get_user_role,
    is_owner,
    list_staff_members,
    remove_staff_role,
    role_label,
    upsert_staff_role,
)


async def _resolve_target_identity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    if update.message and update.message.reply_to_message and update.message.reply_to_message.from_user:
        user = update.message.reply_to_message.from_user
        return user.id, user.first_name, user.username, None

    if not context.args:
        return None, None, None, "Reply to a user or pass a user ID / @username."

    raw_target = context.args[0].strip()
    if raw_target.startswith("@"):
        try:
            chat = await context.bot.get_chat(raw_target)
            return chat.id, getattr(chat, "first_name", None), getattr(chat, "username", None), None
        except Exception:
            return None, None, None, "I could not find that username."

    if not raw_target.lstrip("-").isdigit():
        return None, None, None, "Target must be a numeric user ID or @username."

    target_id = int(raw_target)
    first_name = None
    username = None

    try:
        chat = await context.bot.get_chat(target_id)
        first_name = getattr(chat, "first_name", None)
        username = getattr(chat, "username", None)
    except Exception:
        db_user = await user_collection.find_one({"id": target_id}, {"first_name": 1, "username": 1})
        if db_user:
            first_name = db_user.get("first_name")
            username = db_user.get("username")
        else:
            pm_user = await pm_users.find_one({"_id": target_id}, {"first_name": 1, "username": 1})
            if pm_user:
                first_name = pm_user.get("first_name")
                username = pm_user.get("username")

    return target_id, first_name, username, None


def _display_name(first_name: Optional[str], username: Optional[str], user_id: int) -> str:
    if first_name:
        return first_name
    if username:
        return f"@{username.lstrip('@')}"
    return str(user_id)


async def _assign_role(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    target_role: str,
) -> None:
    actor_id = update.effective_user.id

    if target_role == ROLE_UPLOADER:
        allowed = await can_manage_uploaders(actor_id)
        denied_text = "Only sudo users, developers, or the owner can add uploaders."
    elif target_role == ROLE_SUDO:
        allowed = await can_manage_sudo(actor_id)
        denied_text = "Only developers or the owner can add sudo users."
    else:
        allowed = await can_manage_dev(actor_id)
        denied_text = "Only the owner can add developers."

    if not allowed:
        await update.message.reply_text(f"❌ {denied_text}")
        return

    target_id, first_name, username, error = await _resolve_target_identity(update, context)
    if error:
        await update.message.reply_text(f"ℹ️ {error}")
        return

    if target_id == actor_id:
        await update.message.reply_text("❌ You cannot change your own role with this command.")
        return

    if is_owner(target_id):
        await update.message.reply_text("❌ The owner role is fixed and cannot be modified here.")
        return

    current_role = await get_user_role(target_id)
    if current_role == target_role:
        await update.message.reply_text(
            f"ℹ️ {_display_name(first_name, username, target_id)} is already a {role_label(target_role)}."
        )
        return

    if target_role == ROLE_UPLOADER and current_role in {ROLE_SUDO, ROLE_DEV}:
        await update.message.reply_text(
            f"❌ {_display_name(first_name, username, target_id)} is currently a {role_label(current_role)}. "
            "Remove the higher role first."
        )
        return

    if target_role == ROLE_SUDO and current_role == ROLE_DEV:
        await update.message.reply_text(
            f"❌ {_display_name(first_name, username, target_id)} is currently a Developer. Remove that role first."
        )
        return

    await upsert_staff_role(
        user_id=target_id,
        role=target_role,
        assigned_by=actor_id,
        username=username,
        first_name=first_name,
    )

    LOGGER.info("Role assigned: %s -> %s by %s", target_id, target_role, actor_id)
    await update.message.reply_text(
        f"✅ {_display_name(first_name, username, target_id)} is now a {role_label(target_role)}."
    )


async def _remove_role(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    target_role: str,
) -> None:
    actor_id = update.effective_user.id

    if target_role == ROLE_UPLOADER:
        allowed = await can_manage_uploaders(actor_id)
        denied_text = "Only sudo users, developers, or the owner can remove uploaders."
    elif target_role == ROLE_SUDO:
        allowed = await can_manage_sudo(actor_id)
        denied_text = "Only developers or the owner can remove sudo users."
    else:
        allowed = await can_manage_dev(actor_id)
        denied_text = "Only the owner can remove developers."

    if not allowed:
        await update.message.reply_text(f"❌ {denied_text}")
        return

    target_id, first_name, username, error = await _resolve_target_identity(update, context)
    if error:
        await update.message.reply_text(f"ℹ️ {error}")
        return

    if target_id == actor_id:
        await update.message.reply_text("❌ You cannot remove your own role with this command.")
        return

    if is_owner(target_id):
        await update.message.reply_text("❌ The owner role cannot be removed.")
        return

    current_role = await get_user_role(target_id)
    if current_role != target_role:
        await update.message.reply_text(
            f"ℹ️ {_display_name(first_name, username, target_id)} is not a {role_label(target_role)}."
        )
        return

    removed = await remove_staff_role(target_id, expected_role=target_role)
    if not removed:
        await update.message.reply_text("❌ Failed to remove the role. Please try again.")
        return

    LOGGER.info("Role removed: %s from %s by %s", target_role, target_id, actor_id)
    await update.message.reply_text(
        f"✅ {_display_name(first_name, username, target_id)} is now a Normal User."
    )


def _format_role_section(title: str, members: list[dict], empty_text: str) -> str:
    if not members:
        return f"<b>{escape(title)}</b>\n• {escape(empty_text)}"

    lines = [f"<b>{escape(title)}</b>"]
    for member in members:
        name = escape(format_staff_name(member))
        lines.append(f"• <a href='tg://user?id={member['user_id']}'>{name}</a> - <code>{member['user_id']}</code>")
    return "\n".join(lines)


async def adduploader_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _assign_role(update, context, ROLE_UPLOADER)


async def rmuploader_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _remove_role(update, context, ROLE_UPLOADER)


async def addsudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _assign_role(update, context, ROLE_SUDO)


async def rmsudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _remove_role(update, context, ROLE_SUDO)


async def adddev_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _assign_role(update, context, ROLE_DEV)


async def rmdev_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _remove_role(update, context, ROLE_DEV)


async def sudolist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    actor_id = update.effective_user.id
    if not await can_view_staff(actor_id):
        await update.message.reply_text("❌ Only uploader, sudo, developer, or owner can use this command.")
        return

    owner_name = "Owner"
    owner_id = Config.OWNER_ID

    try:
        owner_chat = await context.bot.get_chat(owner_id)
        owner_name = getattr(owner_chat, "first_name", None) or getattr(owner_chat, "username", None) or "Owner"
    except Exception:
        db_user = await user_collection.find_one({"id": owner_id}, {"first_name": 1, "username": 1})
        if db_user:
            owner_name = db_user.get("first_name") or db_user.get("username") or "Owner"
    owner_link = f"<a href='tg://user?id={owner_id}'>{escape(str(owner_name))}</a> - <code>{owner_id}</code>"

    developers = await list_staff_members(ROLE_DEV)
    sudo_users = await list_staff_members(ROLE_SUDO)
    uploaders = await list_staff_members(ROLE_UPLOADER)

    text = "\n\n".join(
        [
            "<b>🌟 Staff Role List</b>",
            f"<b>{escape(role_label(ROLE_OWNER))}</b>\n• {owner_link}",
            _format_role_section("Developers", developers, "No developers added."),
            _format_role_section("Sudo Users", sudo_users, "No sudo users added."),
            _format_role_section("Uploaders", uploaders, "No uploaders added."),
        ]
    )

    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


application.add_handler(CommandHandler(["adduploader", "adduploder"], adduploader_command, block=False))
application.add_handler(CommandHandler(["rmuploader", "rmuploder"], rmuploader_command, block=False))
application.add_handler(CommandHandler("addsudo", addsudo_command, block=False))
application.add_handler(CommandHandler("rmsudo", rmsudo_command, block=False))
application.add_handler(CommandHandler("adddev", adddev_command, block=False))
application.add_handler(CommandHandler("rmdev", rmdev_command, block=False))
application.add_handler(CommandHandler("sudolist", sudolist_command, block=False))

# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
