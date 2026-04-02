# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import time
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from senpai import application
from senpai.security import is_owner

async def ping(update: Update, context: CallbackContext) -> None:
    """
    ᴘɪɴɢ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ.
    ʀᴇsᴛʀɪᴄᴛᴇᴅ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴏɴʟʏ.
    """
    user_id = update.effective_user.id
    
    # ᴄʜᴇᴄᴋ ɪғ ᴜsᴇʀ ɪs ᴛʜᴇ ᴏᴡɴᴇʀ
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ʀᴇsᴛʀɪᴄᴛᴇᴅ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴏɴʟʏ."
        )
        return

    try:
        start_time = time.time()
        message = await update.message.reply_text("🏓 ᴘᴏɴɢ!")
        end_time = time.time()
        
        # ᴄᴀʟᴄᴜʟᴀᴛᴇ ʟᴀᴛᴇɴᴄʏ
        latency = round((end_time - start_time) * 1000, 2)
        
        # ᴇᴅɪᴛ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ʟᴀᴛᴇɴᴄʏ ɪɴғᴏ
        await message.edit_text(
            f"🏓 **ᴘᴏɴɢ!**\n"
            f"📊 ʟᴀᴛᴇɴᴄʏ: `{latency}ᴍs`\n"
            f"⚡ sᴛᴀᴛᴜs: "
            f"{'ᴇxᴄᴇʟʟᴇɴᴛ' if latency < 100 else 'ɢᴏᴏᴅ' if latency < 300 else 'ғᴀɪʀ'}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ ᴇʀʀᴏʀ: {str(e)}")

# ᴀᴅᴅ ʜᴀɴᴅʟᴇʀ
application.add_handler(CommandHandler("ping", ping))

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
