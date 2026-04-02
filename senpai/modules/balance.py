# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import time
import uuid
import re
from html import escape
from typing import Optional, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User, Chat
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from pymongo import ReturnDocument

from senpai import application, user_collection, LOGGER
from senpai.security import is_owner
from senpai.utils import to_small_caps

pending_payments: Dict[str, Dict[str, Any]] = {}
pay_cooldowns: Dict[int, float] = {}

PENDING_EXPIRY_SECONDS = 5 * 60
PAY_COOLDOWN_SECONDS = 60

async def validate_payment_target(target_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, Optional[str]]:
    try:
        target_chat = await context.bot.get_chat(target_id)
        if hasattr(target_chat, 'type') and target_chat.type == 'private':
            try:
                if hasattr(target_chat, 'is_bot') and target_chat.is_bot:
                    return False, f"🤖 <b>{to_small_caps('Bot Target Detected!')}</b>\n\n⚠️ <i>Bots don't need coins! Pay a real user instead.</i>"
            except:
                pass
        
        if target_chat.type in ['channel', 'group', 'supergroup']:
            return False, f"📢 <b>{to_small_caps('Invalid Target!')}</b>\n\n⚠️ <i>You can only send coins to actual users, not channels or groups.</i>"

        return True, None
    except Exception as e:
        LOGGER.error(f"Error validating payment target {target_id}: {e}")
        return False, f"❌ <b>{to_small_caps('Invalid Target User!')}</b>\n\n⚠️ <i>Please ensure you're paying a valid member of the group.</i>"

async def _ensure_balance_doc(user_id: int) -> Dict[str, Any]:
    try:
        await user_collection.update_one(
            {"id": user_id},
            {
                "$setOnInsert": {
                    "id": user_id,
                    "balance": 0,
                    "characters": [],
                    "favorites": []
                }
            },
            upsert=True,
        )
        doc = await user_collection.find_one({"id": user_id})
        return doc or {"id": user_id, "balance": 0}
    except Exception:
        LOGGER.exception("Error ensuring balance doc for %s", user_id)
        return {"id": user_id, "balance": 0}

async def get_balance(user_id: int) -> int:
    doc = await _ensure_balance_doc(user_id)
    return int(doc.get("balance", 0))

async def change_balance(user_id: int, amount: int) -> int:
    if amount == 0:
        return await get_balance(user_id)

    try:
        await user_collection.update_one(
            {"id": user_id}, 
            {"$inc": {"balance": int(amount)}}, 
            upsert=True
        )
        doc = await user_collection.find_one({"id": user_id})
        new_balance = int(doc.get("balance", 0)) if doc else 0
        LOGGER.debug(f"✅ Balance changed for user {user_id}: {amount:+d} -> new balance: {new_balance}")
        return new_balance
    except Exception:
        LOGGER.exception("Failed to change balance for %s by %s", user_id, amount)
        raise

async def _atomic_transfer(sender_id: int, receiver_id: int, amount: int) -> bool:
    if amount <= 0:
        return False

    try:
        sender_after = await user_collection.find_one_and_update(
            {"id": sender_id, "balance": {"$gte": amount}},
            {"$inc": {"balance": -amount}},
            return_document=ReturnDocument.AFTER,
        )
    except Exception:
        LOGGER.exception("Error decrementing balance for sender %s", sender_id)
        return False

    if sender_after is None:
        LOGGER.warning(f"Transfer failed: sender {sender_id} has insufficient balance")
        return False

    try:
        await user_collection.update_one(
            {"id": receiver_id}, 
            {"$inc": {"balance": amount}}, 
            upsert=True
        )
        LOGGER.debug(f"✅ Transfer successful: {sender_id} -> {receiver_id}, amount: {amount}")
        return True
    except Exception:
        LOGGER.exception("Failed to increment receiver %s; attempting rollback to sender %s", receiver_id, sender_id)
        try:
            await user_collection.update_one(
                {"id": sender_id}, 
                {"$inc": {"balance": amount}}, 
                upsert=True
            )
            LOGGER.debug(f"✅ Rollback successful for sender {sender_id}")
        except Exception:
            LOGGER.exception("❌ Rollback failed for sender %s after transfer failure", sender_id)
        return False

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = update.effective_user
    if context.args:
        arg = context.args[0]
        if arg.isdigit():
            try:
                target = await context.bot.get_chat(int(arg))
            except Exception:
                target = update.effective_user
        elif arg.startswith("@"):
            try:
                target = await context.bot.get_chat(arg)
            except Exception:
                target = update.effective_user
    elif update.message and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user

    user_id = getattr(target, "id", update.effective_user.id)
    bal = await get_balance(user_id)
    name = escape(getattr(target, "first_name", str(user_id)))

    message = f"💰 <b>{to_small_caps('Balance')}:</b> <b>{bal:,}</b> {to_small_caps('coins')}"
    await update.message.reply_text(message, parse_mode="HTML")

async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args and not update.message.reply_to_message:
        usage_text = f"ℹ️ <b>{to_small_caps('Usage')}</b>: <code>/pay &lt;amount&gt;</code>\n\n<i>Reply to a user's message to pay them.</i>"
        await update.message.reply_text(usage_text, parse_mode="HTML")
        return

    sender = update.effective_user

    now = time.time()
    next_allowed = pay_cooldowns.get(sender.id, 0)
    if now < next_allowed:
        remaining = int(next_allowed - now)
        await update.message.reply_text(f"⏳ <b>{to_small_caps('Cooldown Active!')}</b>\n\n⏱️ <i>Please wait <b>{remaining}s</b> before making another payment.</i>", parse_mode="HTML")
        return

    target_id: Optional[int] = None
    amount_str: Optional[str] = None

    if update.message.reply_to_message and len(context.args) == 1:
        target_id = update.message.reply_to_message.from_user.id
        amount_str = context.args[0]
    else:
        if len(context.args) < 2:
            usage_text = f"ℹ️ <b>{to_small_caps('Usage')}</b>: <code>/pay &lt;@username/id&gt; &lt;amount&gt;</code>\n\n<i>Or simply reply to their message with /pay &lt;amount&gt;.</i>"
            await update.message.reply_text(usage_text, parse_mode="HTML")
            return
        raw_target = context.args[0]
        amount_str = context.args[1]
        if raw_target.isdigit():
            target_id = int(raw_target)
        elif raw_target.startswith("@"):
            try:
                chat = await context.bot.get_chat(raw_target)
                target_id = chat.id
            except Exception:
                target_id = None

    if not target_id:
        await update.message.reply_text(f"❌ <b>{to_small_caps('User Not Found!')}</b>\n\n⚠️ <i>Please mention a valid <code>@username</code>, User ID, or reply directly to their message.</i>", parse_mode="HTML")
        return

    if target_id == sender.id:
        await update.message.reply_text(f"🛑 <b>{to_small_caps('Action Denied!')}</b>\n\n⚠️ <i>You cannot send coins to yourself!</i>", parse_mode="HTML")
        return

    is_valid, error_msg = await validate_payment_target(target_id, context)
    if not is_valid:
        await update.message.reply_text(error_msg, parse_mode="HTML")
        return

    try:
        amount = int(amount_str)
    except Exception:
        await update.message.reply_text(f"❌ <b>{to_small_caps('Invalid Amount!')}</b>\n\n⚠️ <i>Please enter a valid positive number for the amount.</i>", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text(f"❌ <b>{to_small_caps('Invalid Amount!')}</b>\n\n⚠️ <i>The amount must be greater than zero.</i>", parse_mode="HTML")
        return

    bal = await get_balance(sender.id)
    if bal < amount:
        await update.message.reply_text(f"❌ <b>{to_small_caps('Insufficient Funds!')}</b>\n\n💸 <i>You don't have enough coins for this transaction.</i>\n💰 <b>Your Balance:</b> {bal:,} coins", parse_mode="HTML")
        return

    token = uuid.uuid4().hex
    created_at = time.time()
    pending_payments[token] = {
        "sender_id": sender.id,
        "target_id": target_id,
        "amount": amount,
        "created_at": created_at,
        "chat_id": update.effective_chat.id,
    }

    try:
        target_chat = await context.bot.get_chat(target_id)
        target_name = escape(getattr(target_chat, "first_name", str(target_id)))
    except Exception:
        target_name = str(target_id)

    sender_name = escape(getattr(sender, "first_name", str(sender.id)))

    text = f"Ŧ <b>{amount:,}</b> {to_small_caps('tokens have been deducted from your account.')}\n\n" \
           f"{to_small_caps('Confirm to send to')} <a href='tg://user?id={target_id}'>{target_name}</a>{to_small_caps(', or cancel to get your tokens back.')}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"✅ {to_small_caps('Confirm')}", callback_data=f"pay_confirm:{token}"),
            InlineKeyboardButton(f"❌ {to_small_caps('Cancel')}", callback_data=f"pay_cancel:{token}")
        ]
    ])

    msg = await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    pending_payments[token]["message_id"] = msg.message_id

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("pay_confirm:") and not data.startswith("pay_cancel:"):
        return

    action, token = data.split(":", 1)
    pending = pending_payments.get(token)
    if not pending:
        try:
            await query.edit_message_text("⏳ <b>This payment request has expired or is invalid.</b>", parse_mode="HTML")
        except Exception:
            pass
        return

    sender_id = pending["sender_id"]
    target_id = pending["target_id"]
    amount = pending["amount"]
    created_at = pending["created_at"]

    user_who_clicked = query.from_user.id
    if user_who_clicked != sender_id:
        await query.answer("⚠️ Only the payment initiator can confirm or cancel this payment.", show_alert=True)
        return

    if time.time() - created_at > PENDING_EXPIRY_SECONDS:
        try:
            await query.edit_message_text("⏳ <b>Payment request expired.</b>", parse_mode="HTML")
        except Exception:
            pass
        pending_payments.pop(token, None)
        return

    if action == "pay_cancel":
        try:
            await query.edit_message_text(f"❌ <b>{to_small_caps('Payment Cancelled')}</b>\n\n⚠️ <i>The transaction has been cancelled by the sender.</i>", parse_mode="HTML")
        except Exception:
            pass
        pending_payments.pop(token, None)
        return

    now = time.time()
    next_allowed = pay_cooldowns.get(sender_id, 0)
    if now < next_allowed:
        remaining = int(next_allowed - now)
        try:
            await query.edit_message_text(f"⏳ <b>{to_small_caps('Cooldown Active!')}</b>\n\n⏱️ <i>Please wait <b>{remaining}s</b> before making another payment.</i>", parse_mode="HTML")
        except Exception:
            pass
        pending_payments.pop(token, None)
        return

    success = await _atomic_transfer(sender_id, target_id, amount)
    if not success:
        try:
            await query.edit_message_text(f"❌ <b>{to_small_caps('Transaction Failed!')}</b>\n\n⚠️ <i>Insufficient funds or internal error occurred.</i>", parse_mode="HTML")
        except Exception:
            pass
        pending_payments.pop(token, None)
        return

    pay_cooldowns[sender_id] = time.time() + PAY_COOLDOWN_SECONDS

    try:
        new_balance = await get_balance(sender_id)
        target_chat = await context.bot.get_chat(target_id)
        target_name = escape(getattr(target_chat, "first_name", str(target_id)))
        confirmed_text = f"✅ {to_small_caps('You paid')} <b>{amount:,}</b> {to_small_caps('coins to')} <a href='tg://user?id={target_id}'>{target_name}</a>.\n" \
                         f"💰 {to_small_caps('Your New Balance')}: <b>{new_balance:,}</b> {to_small_caps('coins')}"
        await query.edit_message_text(confirmed_text, parse_mode="HTML")
    except Exception:
        pass

    pending_payments.pop(token, None)

async def admin_addbal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("❌ <b>Not Authorized.</b>", parse_mode="HTML")
        return

    if len(context.args) < 2:
        await update.message.reply_text("ℹ️ <b>Usage:</b> <code>/addbal &lt;user_id&gt; &lt;amount&gt;</code>", parse_mode="HTML")
        return

    try:
        target = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ <b>Invalid arguments.</b>", parse_mode="HTML")
        return

    try:
        new_bal = await change_balance(target, amount)
        message = f"✅ <b>Updated balance for</b> <a href='tg://user?id={target}'>User</a>: <b>{new_bal:,}</b> {to_small_caps('coins')}"
        await update.message.reply_text(message, parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ <b>Failed to update balance.</b>", parse_mode="HTML")

application.add_handler(CommandHandler(["balance", "bal"], balance_cmd, block=False))
application.add_handler(CommandHandler("pay", pay_cmd, block=False))
application.add_handler(CallbackQueryHandler(pay_callback, pattern=r"^pay_", block=False))
application.add_handler(CommandHandler("addbal", admin_addbal_cmd, block=False))

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
