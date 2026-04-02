# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import random
import secrets
import string
from datetime import datetime, timezone, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from senpai import application, user_collection, db, LOGGER
from senpai.utils import to_small_caps
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
        except:
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

claim_codes_collection = db.claim_codes

ENABLE_MEMBERSHIP_CHECK = True

def generate_coin_code(length: int = 8) -> str:
   alphabet = string.ascii_uppercase + string.digits
   alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('L', '').replace('1', '')
   random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
   return f"COIN-{random_part}"

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

   lock = get_lock(user_id, "claim")
   async with lock:
       can_claim = await check_cooldown(user_id, "claim")
       if not can_claim:
           remaining_time = await get_cooldown_time(user_id, "claim")
           await send_cooldown_message(update, remaining_time)
           return

       coin_amount = random.randint(1000, 3000)
       coin_code = generate_coin_code()

       max_attempts = 10
       for _ in range(max_attempts):
           if not await claim_codes_collection.find_one({"code": coin_code}):
               break
           coin_code = generate_coin_code()

       now = datetime.now(timezone.utc)

       try:
           await claim_codes_collection.insert_one({
               "code": coin_code,
               "user_id": user_id,
               "amount": coin_amount,
               "created_at": now,
               "is_redeemed": False
           })
       except Exception as e:
           LOGGER.error(f"Failed to insert coin code: {e}")
           await update.message.reply_text(
               f"❌ {to_small_caps('Failed to generate code. Please try again.')}"
           )
           return

       await user_collection.update_one(
           {"id": user_id},
           {"$set": {"last_claim": now}},
           upsert=True
       )

       await update.message.reply_text(
           f"<b>💰 {to_small_caps('COIN CODE GENERATED!')}</b>\n\n"
           f"🎟️ <b>{to_small_caps('Your Code:')}</b> <code>{coin_code}</code>\n"
           f"💎 <b>{to_small_caps('Amount:')}</b> {coin_amount:,} {to_small_caps('coins')}\n\n"
           f"📌 {to_small_caps('Use')} <code>/credeem {coin_code}</code> {to_small_caps('to claim your coins!')}\n"
           f"⏰ {to_small_caps('Valid till Midnight IST')}",
           parse_mode="HTML"
       )

       LOGGER.debug(f"User {user_id} generated coin code {coin_code} for {coin_amount} coins")


async def credeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   user_id = update.effective_user.id

   if len(context.args) < 1:
       usage_msg = (
           f"<b>🎁 {to_small_caps('REDEEM CODE')}</b>\n\n"
           f"📝 {to_small_caps('Usage:')} <code>/credeem &lt;CODE&gt;</code>\n\n"
           f"💡 {to_small_caps('Redeem your coin codes to add coins to your balance!')}"
       )
       await update.message.reply_text(usage_msg, parse_mode="HTML")
       return

   code = context.args[0].upper()

   lock = get_lock(user_id, f"redeem_{code}")
   async with lock:
       code_doc = await claim_codes_collection.find_one({
           "code": code,
           "user_id": user_id
       })

       if not code_doc:
           await update.message.reply_text(
               f"<b>❌ {to_small_caps('INVALID CODE')}</b>\n\n"
               f"⚠️ {to_small_caps('This code does not exist or does not belong to you.')}\n\n"
               f"💡 {to_small_caps('Use /claim to generate a new code!')}",
               parse_mode="HTML"
           )
           return

       if code_doc.get("is_redeemed", False):
           await update.message.reply_text(
               f"<b>❌ {to_small_caps('CODE ALREADY REDEEMED')}</b>\n\n"
               f"⚠️ {to_small_caps('This code has already been used.')}\n\n"
               f"💡 {to_small_caps('Use /claim to generate a new code!')}",
               parse_mode="HTML"
           )
           return

       created_at = _normalize_datetime(code_doc.get("created_at"))
       if created_at:
           # Credeem codes generated by claim also expire at midnight IST conceptually now
           # Check if it was generated on the same IST day
           now_utc = datetime.now(timezone.utc)
           if not is_same_ist_day(created_at, now_utc):
               await update.message.reply_text(
                   f"<b>❌ {to_small_caps('CODE EXPIRED')}</b>\n\n"
                   f"⚠️ {to_small_caps('This code expired at midnight.')}\n\n"
                   f"💡 {to_small_caps('Use /claim to generate a new code!')}",
                   parse_mode="HTML"
               )
               return

       coin_amount = code_doc.get("amount", 0)
       now = datetime.now(timezone.utc)

       redeem_result = await claim_codes_collection.update_one(
           {
               "code": code,
               "user_id": user_id,
               "is_redeemed": False
           },
           {"$set": {"is_redeemed": True, "redeemed_at": now}}
       )

       if redeem_result.matched_count == 0:
           await update.message.reply_text(
               f"<b>❌ {to_small_caps('CODE ALREADY REDEEMED')}</b>\n\n"
               f"⚠️ {to_small_caps('This code has already been used.')}\n\n"
               f"💡 {to_small_caps('Use /claim to generate a new code!')}",
               parse_mode="HTML"
           )
           return

       user_result = await user_collection.find_one_and_update(
           {"id": user_id},
           {
               "$inc": {"balance": coin_amount},
               "$set": {"last_credeem": now}
           },
           upsert=True,
           return_document=True
       )

       new_balance = user_result.get("balance", 0) if user_result else coin_amount

       await update.message.reply_text(
           f"<b>✅ {to_small_caps('CODE REDEEMED SUCCESSFULLY!')}</b>\n\n"
           f"💰 <b>{to_small_caps('Coins Added:')}</b> {coin_amount:,}\n"
           f"💎 <b>{to_small_caps('New Balance:')}</b> {new_balance:,} {to_small_caps('coins')}\n\n"
           f"🎉 {to_small_caps('Enjoy your coins!')}",
           parse_mode="HTML"
       )

       LOGGER.debug(f"User {user_id} redeemed code {code} for {coin_amount} coins")

def register_handlers():
   application.add_handler(CommandHandler("claim", claim_command, block=False))
   application.add_handler(CommandHandler("credeem", credeem_command, block=False))
   LOGGER.info("Claim system handlers registered successfully")

register_handlers()
