# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import random
from html import escape

from pymongo.results import UpdateResult
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ChatMemberHandler, CommandHandler, ContextTypes

from senpai import (
    application,
    BOT_USERNAME,
    GROUP_ID,
    SUPPORT_CHAT,
    UPDATE_CHAT,
    VIDEO_URL,
    user_collection,
)
from senpai import pm_users as collection
from senpai.config import Config
from senpai.modules.ref import ensure_referral_schema, process_referral_start
from senpai.security import ROLE_DEV, ROLE_SUDO, ROLE_UPLOADER, format_staff_name, list_staff_members
from senpai.utils import small_caps


def get_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✦ ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"http://t.me/{BOT_USERNAME}?startgroup=new")],
        [
            InlineKeyboardButton("✧ sᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_CHAT}"),
            InlineKeyboardButton("✧ ᴜᴘᴅᴀᴛᴇs", url=f"https://t.me/{UPDATE_CHAT}"),
        ],
        [
            InlineKeyboardButton("✦ ɢᴜɪᴅᴀɴᴄᴇ", callback_data="help"),
            InlineKeyboardButton("✦ ᴄʀᴇᴅɪᴛs", callback_data="credits_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_caption() -> str:
    return """✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ Sᴇɴᴘᴀɪ Wᴀɪғᴜ Bᴏᴛ ✨

ɪ'ᴍ ᴀɴ Sᴇɴᴘᴀɪ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴄᴀᴛᴄʜᴇʀ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ғᴏʀ ᴜʟᴛɪᴍᴀᴛᴇ ᴄᴏʟʟᴇᴄᴛᴏʀs! 🎴"""


def get_credits_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Developer", callback_data="credits_developer"),
            InlineKeyboardButton("Sudo User", callback_data="credits_sudo"),
        ],
        [
            InlineKeyboardButton("Uploader", callback_data="credits_uploader"),
            InlineKeyboardButton("Owner", callback_data="credits_owner"),
        ],
        [InlineKeyboardButton("Back", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _chunk_buttons(buttons: list[InlineKeyboardButton], size: int = 3) -> list[list[InlineKeyboardButton]]:
    return [buttons[index:index + size] for index in range(0, len(buttons), size)]


def _safe_button_text(name: str) -> str:
    return (name or "Unknown")[:24]


async def _get_owner_buttons(context: ContextTypes.DEFAULT_TYPE) -> list[list[InlineKeyboardButton]]:
    owner_id = Config.OWNER_ID
    owner_name = "Owner"

    try:
        owner_chat = await context.bot.get_chat(owner_id)
        owner_name = getattr(owner_chat, "first_name", None) or getattr(owner_chat, "username", None) or "Owner"
    except Exception:
        owner_doc = await user_collection.find_one({"id": owner_id}, {"first_name": 1, "username": 1})
        if owner_doc:
            owner_name = owner_doc.get("first_name") or owner_doc.get("username") or "Owner"

    return [[InlineKeyboardButton(_safe_button_text(str(owner_name)), url=f"tg://user?id={owner_id}")]]


async def _get_staff_buttons(role: str, context: ContextTypes.DEFAULT_TYPE) -> list[list[InlineKeyboardButton]]:
    if role == "owner":
        rows = await _get_owner_buttons(context)
    else:
        members = await list_staff_members(role)
        if not members:
            rows = [[InlineKeyboardButton("No Users", callback_data="credits_noop")]]
        else:
            buttons = [
                InlineKeyboardButton(
                    _safe_button_text(format_staff_name(member)),
                    url=f"tg://user?id={member['user_id']}",
                )
                for member in members
            ]
            rows = _chunk_buttons(buttons, 3)

    rows.append([InlineKeyboardButton("Back", callback_data="credits_menu")])
    return rows


async def _edit_start_panel(
    query,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    disable_web_page_preview: bool = False,
) -> None:
    try:
        if query.message and query.message.caption is not None:
            await query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=disable_web_page_preview,
            )
    except Exception as exc:
        if "message is not modified" in str(exc).lower():
            return

        try:
            await query.message.delete()
        except Exception:
            pass

        await query.message.chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=disable_web_page_preview,
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.is_bot:
        return

    user_id = user.id
    first_name = user.first_name
    username = user.username

    if update.effective_chat.type == "private":
        try:
            result: UpdateResult = await collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "first_name": first_name,
                        "username": username,
                    },
                    "$setOnInsert": {
                        "started_at": update.message.date if update.message else None,
                    },
                },
                upsert=True,
            )

            if result.upserted_id is not None:
                total_users = await collection.count_documents({})
                username_text = f"@{username}" if username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"

                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"#ʙᴏᴛsᴛᴀʀᴛ\n\n"
                    f"ʙᴏᴛ sᴛᴀʀᴛᴇᴅ\n\n"
                    f"ɴᴀᴍᴇ : <a href='tg://user?id={user_id}'>{escape(first_name or 'User')}</a>\n"
                    f"ɪᴅ : <code>{user_id}</code>\n"
                    f"ᴜsᴇʀɴᴀᴍᴇ : {username_text}\n\n"
                    f"ᴛᴏᴛᴀʟ ᴜsᴇʀs : {total_users}",
                    parse_mode="HTML",
                )

        except Exception as e:
            print(f"Database error in /start: {e}")

        await ensure_referral_schema(user_id, username, first_name)

        args = context.args
        if args and args[0].startswith("ref_"):
            referral_code = args[0][4:]
            await process_referral_start(user_id, referral_code, context)

    video_url = random.choice(VIDEO_URL)
    keyboard = get_keyboard()
    caption = get_main_caption()

    try:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML",
            read_timeout=300,
            write_timeout=300,
            connect_timeout=60,
        )
    except Exception as e:
        print(f"Video send failed: {e}")
        try:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=video_url,
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
                read_timeout=60,
                write_timeout=60,
            )
        except Exception as e2:
            print(f"Animation send failed: {e2}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )


async def track_group_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.my_chat_member
    if not result:
        return

    chat = result.chat
    new_status = result.new_chat_member
    old_status = result.old_chat_member

    if new_status.user.id != context.bot.id:
        return

    if old_status.status in ["left", "kicked"] and new_status.status in ["member", "administrator"]:
        try:
            added_by = result.from_user
            added_by_name = added_by.first_name or "Unknown"
            added_by_link = f"<a href='tg://user?id={added_by.id}'>{escape(added_by_name)}</a>"

            try:
                chat_info = await context.bot.get_chat(chat.id)
                invite_link = chat_info.invite_link
                if not invite_link:
                    try:
                        invite_link = await context.bot.create_chat_invite_link(chat.id)
                        invite_link = invite_link.invite_link
                    except Exception:
                        invite_link = None
            except Exception:
                invite_link = None

            group_link_text = invite_link if invite_link else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"

            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"#ᴀᴅᴅɢʀᴏᴜᴘ\n\n"
                f"ɢʀᴏᴜᴘ ɴᴀᴍᴇ : {escape(chat.title or 'Unknown')}\n"
                f"ɢʀᴏᴜᴘ ɪᴅ : <code>{chat.id}</code>\n"
                f"ɢʀᴏᴜᴘ ᴛʏᴘᴇ : {small_caps(chat.type)}\n"
                f"ɢʀᴏᴜᴘ ʟɪɴᴋ : {group_link_text}\n"
                f"ᴀᴅᴅᴇᴅ ʙʏ : {added_by_link}",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"Error tracking group add: {e}")

    elif old_status.status in ["member", "administrator"] and new_status.status in ["left", "kicked"]:
        try:
            removed_by = result.from_user
            removed_by_name = removed_by.first_name or "Unknown"
            removed_by_link = f"<a href='tg://user?id={removed_by.id}'>{escape(removed_by_name)}</a>"

            try:
                chat_info = await context.bot.get_chat(chat.id)
                invite_link = chat_info.invite_link
            except Exception:
                invite_link = None

            group_link_text = invite_link if invite_link else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"

            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"#ʟᴇғᴛ\n\n"
                f"ɢʀᴏᴜᴘ ɴᴀᴍᴇ : {escape(chat.title or 'Unknown')}\n"
                f"ɢʀᴏᴜᴘ ɪᴅ : <code>{chat.id}</code>\n"
                f"ɢʀᴏᴜᴘ ᴛʏᴘᴇ : {small_caps(chat.type)}\n"
                f"ɢʀᴏᴜᴘ ʟɪɴᴋ : {group_link_text}\n"
                f"ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {removed_by_link}",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"Error tracking group remove: {e}")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "credits_noop":
        return

    if query.data == "help":
        help_text = f"""✦ {small_caps('guidance from senpai')} ✦

✦ ── 『 ʜᴀʀᴇᴍ ᴄᴏᴍᴍᴀɴᴅ ʟɪsᴛ 』 ── ✦

/guess
↳ ɢᴜᴇss ᴛʜᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ

/bal
↳ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ʙᴀʟᴀɴᴄᴇ

/fav
↳ ᴀᴅᴅ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ғᴀᴠᴏʀɪᴛᴇs

/collection
↳ ᴠɪᴇᴡ ʏᴏᴜʀ ʜᴀʀᴇᴍ ᴄᴏʟʟᴇᴄᴛɪᴏɴ

/leaderboard
↳ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴛᴏᴘ ᴜsᴇʀ ʟɪsᴛ

/gift
↳ ɢɪғᴛ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴜsᴇʀ

/trade
↳ ᴛʀᴀᴅᴇ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴡɪᴛʜ ᴀɴᴏᴛʜᴇʀ ᴜsᴇʀ

/shop
↳ ᴏᴘᴇɴ ᴛʜᴇ sʜᴏᴘ

/smode
↳ ᴄʜᴀɴɢᴇ ʜᴀʀᴇᴍ ᴍᴏᴅᴇ

/s
↳ ᴠɪᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀ ғʀᴏᴍ ᴡᴀɪғᴜ ɪᴅ

/find
↳ ғɪɴᴅ ʜᴏᴡ ᴍᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀs ᴇxɪsᴛ ᴡɪᴛʜ ᴀ ɴᴀᴍᴇ

/redeem
↳ ʀᴇᴅᴇᴇᴍ ᴄʜᴀʀᴀᴄᴛᴇʀs ᴀɴᴅ ᴄᴏɪɴs

/sclaim
↳ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴡᴀɪғᴜ

/claim
↳ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴄᴏᴜɴᴛ

/pay
↳ sᴇɴᴅ ᴄᴏɪɴs ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴜsᴇʀ

/referral
↳ ᴠɪᴇᴡ ʀᴇғᴇʀʀᴀʟ ᴅᴀsʜʙᴏᴀʀᴅ

✦ ───────────────── ✦"""

        help_keyboard = [[InlineKeyboardButton("✧ ʀᴇᴛᴜʀɴ", callback_data="back")]]
        await _edit_start_panel(query, help_text, InlineKeyboardMarkup(help_keyboard))
        return

    if query.data == "credits_menu":
        credits_text = (
            "<b>✦ Credits Panel ✦</b>\n\n"
            "Select a role to view the current members."
        )
        await _edit_start_panel(query, credits_text, get_credits_menu_keyboard())
        return

    if query.data in {"credits_developer", "credits_sudo", "credits_uploader", "credits_owner"}:
        role_map = {
            "credits_developer": (ROLE_DEV, "Developer"),
            "credits_sudo": (ROLE_SUDO, "Sudo Users"),
            "credits_uploader": (ROLE_UPLOADER, "Uploaders"),
            "credits_owner": ("owner", "Owner"),
        }
        role_key, title = role_map[query.data]
        buttons = await _get_staff_buttons(role_key, context)
        text = f"<b>✦ {escape(title)} ✦</b>\n\nTap a name to open the profile."
        await _edit_start_panel(query, text, InlineKeyboardMarkup(buttons))
        return

    if query.data == "back":
        await _edit_start_panel(query, get_main_caption(), get_keyboard())


application.add_handler(
    CallbackQueryHandler(
        button,
        pattern=r"^(help|back|credits_menu|credits_noop|credits_developer|credits_sudo|credits_uploader|credits_owner)$",
    )
)
application.add_handler(ChatMemberHandler(track_group_status, ChatMemberHandler.MY_CHAT_MEMBER))
application.add_handler(CommandHandler("start", start))

# (c) @SenpaiLabs
# SenpaiLabs Developer
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
