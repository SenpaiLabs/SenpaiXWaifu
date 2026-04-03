# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from html import escape
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from senpai import application, user_collection, collection, db, LOGGER
from senpai.media import copy_character_media_fields, get_character_media_reference
from senpai.utils import to_small_caps, RARITY_MAP, get_rarity_display, get_rarity_from_string, RARITY_EMOJIS, RARITY_NAMES
from senpai.config import Config
SUPPORT_GROUP = f"https://t.me/{Config.SUPPORT_CHAT}"
SUPPORT_CHANNEL = f"https://t.me/{Config.UPDATE_CHAT}"
SUPPORT_GROUP_REF = f"@{Config.SUPPORT_CHAT}"
SUPPORT_CHANNEL_REF = f"@{Config.UPDATE_CHAT}"

IST = timezone(timedelta(hours=5, minutes=30))

_claim_locks = {}

def get_lock(user_id: int, command_type: str):
    key = f"{user_id}_{command_type}"
    if key not in _claim_locks:
        _claim_locks[key] = asyncio.Lock()
    return _claim_locks[key]

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    user_id = update.effective_user.id
    status = {'group': False, 'channel': False}

    try:
        try:
            group_member = await context.bot.get_chat_member(SUPPORT_GROUP_REF, user_id)
            if group_member.status not in ['left', 'kicked']:
                status['group'] = True
        except Exception as e:
            LOGGER.warning(f"Cannot check support group membership: {e}")
            status['group'] = True

        try:
            channel_member = await context.bot.get_chat_member(SUPPORT_CHANNEL_REF, user_id)
            if channel_member.status not in ['left', 'kicked']:
                status['channel'] = True
        except Exception as e:
            LOGGER.warning(f"Cannot check update channel membership: {e}")
            status['channel'] = True

        return status
    except Exception as e:
        LOGGER.error(f"Error checking membership: {e}")
        return {'group': True, 'channel': True}

async def show_join_buttons(update: Update, missing: dict):
    keyboard = []
    if not missing.get('channel', True):
        keyboard.append([InlineKeyboardButton(to_small_caps("📢 Update Channel"), url=SUPPORT_CHANNEL)])
    if not missing.get('group', True):
        keyboard.append([InlineKeyboardButton(to_small_caps("👥 Support Group"), url=SUPPORT_GROUP)])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    msg_converted = to_small_caps('Join the channel to claim your Daily character')
    await update.message.reply_text(
        f"<b>🔔 {msg_converted}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

def _normalize_datetime(dt):
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception as e:
            LOGGER.warning(f"Failed to parse datetime string '{dt}': {e}")
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _utcnow():
    return datetime.now(timezone.utc)

def get_next_ist_midnight() -> datetime:
    now_utc = _utcnow()
    now_ist = now_utc.astimezone(IST)
    tomorrow_ist = now_ist + timedelta(days=1)
    return tomorrow_ist.replace(hour=0, minute=0, second=0, microsecond=0)

def is_same_ist_day(dt1: datetime, dt2: datetime) -> bool:
    ist1 = dt1.astimezone(IST)
    ist2 = dt2.astimezone(IST)
    return ist1.date() == ist2.date()

async def check_cooldown(user_id: int, command_type: str) -> bool:
    user = await user_collection.find_one(
        {"id": user_id},
        {f"last_{command_type}": 1}
    )

    if not user:
        return True

    last_claim_time = user.get(f"last_{command_type}")
    if not last_claim_time:
        return True

    last_claim_time = _normalize_datetime(last_claim_time)
    if not last_claim_time:
        return True

    now_utc = _utcnow()
    if is_same_ist_day(last_claim_time, now_utc):
        return False

    return True

async def get_cooldown_time(user_id: int, command_type: str) -> Optional[str]:
    user = await user_collection.find_one(
        {"id": user_id},
        {f"last_{command_type}": 1}
    )

    if not user or not user.get(f"last_{command_type}"):
        return None

    last_claim_time = _normalize_datetime(user[f"last_{command_type}"])
    if last_claim_time is None:
        return None

    now_utc = _utcnow()
    if not is_same_ist_day(last_claim_time, now_utc):
        return None

    next_midnight = get_next_ist_midnight()
    remaining = next_midnight - now_utc.astimezone(IST)

    if remaining.total_seconds() <= 0:
        return None

    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)

    return f"{hours}h {minutes}m"

async def send_cooldown_message(update: Update, time_str: str):
    msg_converted = to_small_caps(f"You've already claimed today! Next reward in: {time_str}")
    await update.message.reply_text(
        f"<b>⏳ {msg_converted}</b>",
        parse_mode="HTML"
    )

ENABLE_MEMBERSHIP_CHECK = True
ALLOWED_RARITIES = [2, 3, 4]


async def sclaim_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   chat_id = update.effective_chat.id
   user_id = update.effective_user.id

   if ENABLE_MEMBERSHIP_CHECK:
       membership = await check_membership(update, context)
       missing = {}
       if not membership['group']: missing['group'] = False
       if not membership['channel']: missing['channel'] = False
       
       if missing:
           await show_join_buttons(update, missing)
           return

   chat_username = update.effective_chat.username
   if (chat_username is None or chat_username.lower() != Config.SUPPORT_CHAT.lower()) and chat_id != Config.GROUP_ID:
       keyboard = [[InlineKeyboardButton(to_small_caps("💬 Join Here"), url=SUPPORT_GROUP)]]
       await update.message.reply_text(
           f"<b>❌ {to_small_caps('Incorrect Chat')}</b>\n\n"
           f"{to_small_caps('You can only use this command inside our official support group!')}",
           reply_markup=InlineKeyboardMarkup(keyboard),
           parse_mode="HTML"
       )
       return

   lock = get_lock(user_id, "sclaim")
   async with lock:
       can_claim = await check_cooldown(user_id, "sclaim")
       if not can_claim:
           remaining_time = await get_cooldown_time(user_id, "sclaim")
           await send_cooldown_message(update, remaining_time)
           return

       # Build rarity variants for MongoDB $in query (int, string, emoji, name forms)
       rarity_variants = []
       for r in ALLOWED_RARITIES:
           rarity_variants.append(r)           # int: 2, 3, 4
           rarity_variants.append(str(r))       # str: "2", "3", "4"
           emoji = RARITY_EMOJIS.get(r, '')
           name = RARITY_NAMES.get(r, '')
           if emoji:
               rarity_variants.append(emoji)
           if name:
               rarity_variants.append(name)

       matching_chars = await collection.find(
           {"rarity": {"$in": rarity_variants}},
           {"id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1, "tg_file_id": 1, "_id": 0}
       ).to_list(None)

       if not matching_chars:
           await update.message.reply_text(
               f"❌ {to_small_caps('No characters available at the moment!')}"
           )
           return

       character = random.choice(matching_chars)
       character_id = character.get("id")
       character_name = character.get("name", "Unknown")
       anime_name = character.get("anime", "Unknown")
       rarity = get_rarity_from_string(character.get("rarity", 1))
       media_reference = get_character_media_reference(character)

       from datetime import datetime, timezone
       now = datetime.now(timezone.utc)
       result = await user_collection.update_one(
           {
               "id": user_id,
               "$or": [
                   {f"last_sclaim": {"$exists": False}},
                   {f"last_sclaim": {"$lte": now - timedelta(hours=24)}}
               ]
           },
           {
               "$push": {
                   "characters": copy_character_media_fields(character, {
                       "id": character_id,
                       "name": character_name,
                       "anime": anime_name,
                       "rarity": rarity,
                   })
               },
               "$set": {"last_sclaim": now}
           },
           upsert=True
       )

       if result.matched_count == 0 and result.upserted_id is None:
           remaining_time = await get_cooldown_time(user_id, "sclaim")
           await send_cooldown_message(update, remaining_time)
           return

       rarity_display = get_rarity_display(rarity)

       message = (
           f"<b>🎉 {to_small_caps('CONGRATULATIONS!')}</b>\n\n"
           f"🎴 <b>{to_small_caps('Character:')}</b> {escape(character_name)}\n"
           f"📺 <b>{to_small_caps('Anime:')}</b> {escape(anime_name)}\n"
           f"⭐ <b>{to_small_caps('Rarity:')}</b> {rarity_display}\n"
           f"🆔 <b>{to_small_caps('ID:')}</b> {character_id}\n\n"
           f"✅ {to_small_caps('Character has been added to your collection!')}"
       )

       if media_reference:
           try:
               await update.message.reply_photo(
                   photo=media_reference,
                   caption=message,
                   parse_mode="HTML"
               )
           except Exception as e:
               LOGGER.error(f"Failed to send image: {e}")
               await update.message.reply_text(message, parse_mode="HTML")
       else:
           await update.message.reply_text(message, parse_mode="HTML")

       LOGGER.debug(f"User {user_id} claimed character {character_id} ({character_name}) via /sclaim")


def register_handlers():
   application.add_handler(CommandHandler("sclaim", sclaim_command, block=False))
   LOGGER.info("Sclaim system handler registered successfully")


register_handlers()

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
