# (c) @SenpaiLabs
# SenpaiLabs Developer 

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from senpai import application, user_collection, LOGGER
from senpai.character_ids import character_matches_id

async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ: /fav <ɪᴅ>")
        return

    try:
        character_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.")
        return

    try:
        user = await user_collection.find_one({'id': user_id})
    except Exception:
        LOGGER.exception("Failed to fetch user for fav")
        user = None

    if not user or not user.get('characters'):
        await update.message.reply_text("ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ʏᴇᴛ.")
        return

    character = next((c for c in user['characters'] if character_matches_id(c, character_id)), None)
    if not character:
        await update.message.reply_text("ᴛʜᴀᴛ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪꜱ ɴᴏᴛ ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ.")
        return

    try:
        await user_collection.update_one({'id': user_id}, {'$addToSet': {'favorites': character_id}})
        await update.message.reply_text(
            f"ᴄʜᴀʀᴀᴄᴛᴇʀ {character.get('name')} ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇꜱ."
        )
    except Exception:
        LOGGER.exception("Failed to set favorite character")
        await update.message.reply_text("ꜰᴀɪʟᴇᴅ ᴛᴏ ᴍᴀʀᴋ ꜰᴀᴠᴏʀɪᴛᴇ. ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")

async def unfav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ: /unfav <ɪᴅ>")
        return

    try:
        character_id = int(args[0])
    except ValueError:
        await update.message.reply_text("ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.")
        return

    try:
        user = await user_collection.find_one({'id': user_id})
    except Exception:
        LOGGER.exception("Failed to fetch user for unfav")
        user = None

    if not user or not user.get('characters'):
        await update.message.reply_text("ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ʏᴇᴛ.")
        return

    favorites = user.get('favorites', [])
    if character_id not in favorites:
        await update.message.reply_text("ᴛʜᴀᴛ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪꜱ ɴᴏᴛ ɪɴ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇꜱ.")
        return

    try:
        await user_collection.update_one({'id': user_id}, {'$pull': {'favorites': character_id}})
        await update.message.reply_text(
            f"ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ {character_id} ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇꜱ."
        )
    except Exception:
        LOGGER.exception("Failed to remove favorite character")
        await update.message.reply_text("ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ꜰᴀᴠᴏʀɪᴛᴇ. ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")

application.add_handler(CommandHandler("fav", fav, block=False))
application.add_handler(CommandHandler("unfav", unfav, block=False))
