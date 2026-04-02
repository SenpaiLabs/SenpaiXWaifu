# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import io
import logging
import random
import asyncio
from enum import Enum
from functools import wraps
from datetime import datetime

from pymongo import ReturnDocument
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext

from senpai import application, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT
from senpai.character_ids import character_id_query, format_character_id, normalize_character_id
from senpai.config import Config
from senpai.security import is_owner_or_sudo
from senpai.utils import to_small_caps

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RarityLevel(Enum):
    COMMON = (1, "⚪ ᴄᴏᴍᴍᴏɴ")
    RARE = (2, "🔵 ʀᴀʀᴇ")
    LEGENDARY = (3, "🟡 ʟᴇɢᴇɴᴅᴀʀʏ")
    SPECIAL = (4, "💮 ꜱᴘᴇᴄɪᴀʟ")
    ANCIENT = (5, "👹 ᴀɴᴄɪᴇɴᴛ")
    CELESTIAL = (6, "🎐 ᴄᴇʟᴇꜱᴛɪᴀʟ")
    EPIC = (7, "🔮 ᴇᴘɪᴄ")
    COSMIC = (8, "🪐 ᴄᴏꜱᴍɪᴄ")
    NIGHTMARE = (9, "⚰️ ɴɪɢʜᴛᴍᴀʀᴇ")
    FROSTBORN = (10, "🌬️ ꜰʀᴏꜱᴛʙᴏʀɴ")
    VALENTINE = (11, "💝 ᴠᴀʟᴇɴᴛɪɴᴇ")
    SPRING = (12, "🌸 ꜱᴘʀɪɴɢ")
    TROPICAL = (13, "🏖️ ᴛʀᴏᴘɪᴄᴀʟ")
    KAWAII = (14, "🍭 ᴋᴀᴡᴀɪɪ")
    HYBRID = (15, "🧬 ʜʏʙʀɪᴅ")

    @classmethod
    def get_by_number(cls, number):
        for rarity in cls:
            if rarity.value[0] == number:
                return rarity
        return None

WRONG_FORMAT_TEXT = f"""<b>{to_small_caps('Example')}:</b>
<code>/upload naruto-uzumaki naruto 3</code>

<b>{to_small_caps('Available Rarities')}:</b>
1 - ⚪ ᴄᴏᴍᴍᴏɴ
2 - 🔵 ʀᴀʀᴇ
3 - 🟡 ʟᴇɢᴇɴᴅᴀʀʏ
4 - 💮 ꜱᴘᴇᴄɪᴀʟ
5 - 👹 ᴀɴᴄɪᴇɴᴛ
6 - 🎐 ᴄᴇʟᴇꜱᴛɪᴀʟ
7 - 🔮 ᴇᴘɪᴄ
8 - 🪐 ᴄᴏꜱᴍɪᴄ
9 - ⚰️ ɴɪɢʜᴛᴍᴀʀᴇ
10 - 🌬️ ꜰʀᴏꜱᴛʙᴏʀɴ
11 - 💝 ᴠᴀʟᴇɴᴛɪɴᴇ
12 - 🌸 ꜱᴘʀɪɴɢ
13 - 🏖️ ᴛʀᴏᴘɪᴄᴀʟ
14 - 🍭 ᴋᴀᴡᴀɪɪ
15 - 🧬 ʜʏʙʀɪᴅ"""

def admin_only(func):
    """Check if user is owner or sudo user"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_owner_or_sudo(user_id):
            await update.message.reply_text('⛔ You do not have permission to use this command.')
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def log_command(func):
    """Log command usage"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        command = update.message.text.split()[0] if update.message.text else "unknown"
        logger.debug(f"Command {command} used by {user.id} ({user.username or user.first_name})")
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {command}: {str(e)}", exc_info=True)
            raise
    return wrapper

class ImageUploader:
    def __init__(self):
        self.imgbb_key = Config.IMGBB_API_KEY
        self.services = [
            self._upload_to_telegraph,
            self._upload_to_catbox,
        ]
        if self.imgbb_key:
            self.services.insert(0, self._upload_to_imgbb)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _upload_to_imgbb(self, image_data: bytes) -> str:
        """Upload to ImgBB with retry"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('image', io.BytesIO(image_data))
                data.add_field('key', self.imgbb_key)
                
                async with session.post(
                    "https://api.imgbb.com/1/upload", 
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            logger.debug("ImgBB upload successful")
                            return result['data']['url']
                    elif response.status == 429:
                        logger.warning("ImgBB rate limited, will retry...")
                        raise Exception("Rate limited")
        except Exception as e:
            logger.warning(f"ImgBB attempt failed: {e}")
            raise
        return None

    async def _upload_to_telegraph(self, image_data: bytes) -> str:
        """Upload to Telegraph"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', io.BytesIO(image_data), filename='image.jpg')
                
                async with session.post(
                    "https://telegra.ph/upload",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            logger.debug("Telegraph upload successful")
                            return f"https://telegra.ph{result[0]['src']}"
        except Exception as e:
            logger.warning(f"Telegraph upload failed: {e}")
        return None

    async def _upload_to_catbox(self, image_data: bytes) -> str:
        """Upload to Catbox"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('fileToUpload', io.BytesIO(image_data), filename='image.jpg')
                
                async with session.post(
                    "https://catbox.moe/user/api.php",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        url = await response.text()
                        if url and url.startswith('http'):
                            logger.debug("Catbox upload successful")
                            return url.strip()
        except Exception as e:
            logger.warning(f"Catbox upload failed: {e}")
        return None

    async def upload_with_failover(self, image_data: bytes) -> str:
        """Try multiple services until one succeeds"""
        services = self.services.copy()
        random.shuffle(services)
        
        for service in services:
            try:
                url = await service(image_data)
                if url:
                    return url
            except Exception as e:
                logger.error(f"Service {service.__name__} failed: {e}")
                continue
        
        return None

async def get_next_sequence_number(sequence_name):
    """Get the next numeric character ID."""
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(sequence_document['sequence_value'])

@admin_only
@log_command
async def upload(update: Update, context: CallbackContext) -> None:
    """Enhanced upload command with progress tracking"""
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            '❌ Please reply to an image with the upload command!\n\n' + WRONG_FORMAT_TEXT,
            parse_mode='HTML'
        )
        return

    if not update.message.reply_to_message.photo:
        await update.message.reply_text('❌ The replied message must contain an image!')
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text(WRONG_FORMAT_TEXT, parse_mode='HTML')
        return

    progress_msg = await update.message.reply_text(f'⏳ <b>{to_small_caps("Starting upload process...")}</b>', parse_mode='HTML')

    try:
        character_name = args[0].replace('-', ' ').strip().title()
        anime_name = args[1].replace('-', ' ').strip().title()

        try:
            rarity_number = int(args[2])
        except ValueError:
            await progress_msg.edit_text('❌ Rarity must be a number between 1-15.')
            return

        rarity_level = RarityLevel.get_by_number(rarity_number)
        if not rarity_level:
            await progress_msg.edit_text(f'❌ Invalid rarity number.\n\n{WRONG_FORMAT_TEXT}', parse_mode='HTML')
            return

        rarity = rarity_level.value[1]

        await progress_msg.edit_text(f'📥 <b>{to_small_caps("Downloading image")}...</b>', parse_mode='HTML')
        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB check
            await progress_msg.edit_text('❌ Image too large! Max size: 10MB')
            return

        await progress_msg.edit_text(f'☁️ <b>{to_small_caps("Uploading to cloud storage")}...</b>\n<i>This may take a few seconds...</i>', parse_mode='HTML')
        
        uploader = ImageUploader()
        img_url = await uploader.upload_with_failover(bytes(image_bytes))
        
        if not img_url:
            await progress_msg.edit_text('❌ Failed to upload image. All hosting services failed.\nPlease try again later.')
            return

        await progress_msg.edit_text(f'💾 <b>{to_small_caps("Saving to database")}...</b>', parse_mode='HTML')
        
        char_id = await get_next_sequence_number('character_id')
        display_char_id = format_character_id(char_id)
        
        character = {
            'img_url': img_url,
            'name': character_name,
            'anime': anime_name,
            'rarity': rarity,
            'id': char_id,
            'created_at': datetime.utcnow(),
            'added_by': update.effective_user.id,
            'added_by_name': update.effective_user.first_name
        }
        
        rarity_parts = rarity.split(' ', 1)
        rarity_emoji = rarity_parts[0] if len(rarity_parts) > 1 else "⚪"
        rarity_text = rarity_parts[1].title() if len(rarity_parts) > 1 else rarity

        channel_caption = (
            f'<code>{display_char_id}</code>: {character_name}\n'
            f'{anime_name}\n'
            f'{rarity_emoji} 𝙍𝘼𝙍𝙄𝙏𝙔: {rarity_text}\n'
            f'Type: 🖼 Image\n\n'
            f'𝑴𝒂𝒅𝒆 𝑩𝒚 ➥ <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>'
        )

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=channel_caption,
                parse_mode='HTML',
                read_timeout=60,
                write_timeout=60,
                connect_timeout=60,
                pool_timeout=60
            )
            character['message_id'] = message.message_id
            
        except Exception as e:
            logger.error(f"Channel post failed with URL: {e}")
            await progress_msg.edit_text(f'⚠️ <b>{to_small_caps("URL failed, sending image directly")}...</b>', parse_mode='HTML')
            
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=io.BytesIO(image_bytes),
                caption=channel_caption,
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id

        await collection.insert_one(character)
        
        channel_username = str(CHARA_CHANNEL_ID)[4:] if str(CHARA_CHANNEL_ID).startswith('-100') else CHARA_CHANNEL_ID
        
        await progress_msg.delete()
        await update.message.reply_text(
            f'✅ <b>{to_small_caps("Character Added Successfully!")}</b>',
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        logger.debug(f"Character {char_id} ({character_name}) added successfully by {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        await progress_msg.edit_text(
            f'❌ <b>Upload Failed!</b>\n\n'
            f'Error: <code>{str(e)[:100]}</code>\n\n'
            f'If this persists, contact: {SUPPORT_CHAT}',
            parse_mode='HTML'
        )

@admin_only
@log_command
async def delete(update: Update, context: CallbackContext) -> None:
    """Enhanced delete command"""
    args = context.args
    if len(args) != 1:
        await update.message.reply_text(
            '❌ <b>Incorrect format!</b>\n\n'
            '<b>Usage:</b> <code>/delete ID</code>\n'
            '<b>Example:</b> <code>/delete 042</code>',
            parse_mode='HTML'
        )
        return

    char_id = normalize_character_id(args[0])
    if char_id is None:
        await update.message.reply_text('❌ Character ID must be a number.')
        return
    
    try:
        character = await collection.find_one(character_id_query(char_id))
        
        if not character:
            await update.message.reply_text(
                f'❌ Character with ID <code>{format_character_id(char_id)}</code> not found.',
                parse_mode='HTML'
            )
            return
        display_char_id = format_character_id(character.get('id', char_id))
        
        if character.get('message_id'):
            try:
                await context.bot.delete_message(
                    chat_id=CHARA_CHANNEL_ID,
                    message_id=character['message_id']
                )
                logger.debug(f"Deleted message {character['message_id']} from channel")
            except Exception as e:
                logger.warning(f"Could not delete message from channel: {e}")
        
        await collection.delete_one(character_id_query(char_id))
        
        await update.message.reply_text(
            f'✅ <b>{to_small_caps("Character Deleted Successfully!")}</b>\n\n'
            f'🆔 <b>{to_small_caps("ID")}:</b> <code>{display_char_id}</code>',
            parse_mode='HTML'
        )
        logger.debug(f"Character {char_id} deleted by {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        await update.message.reply_text(f'❌ Error: {str(e)[:200]}')

@admin_only
@log_command
async def update(update: Update, context: CallbackContext) -> None:
    """Enhanced update command"""
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            '❌ <b>Incorrect format!</b>\n\n'
            '<b>Usage:</b> <code>/update ID field new_value</code>\n\n'
            '<b>Fields:</b> name, anime, rarity, img_url\n\n'
            '<b>Examples:</b>\n'
            '<code>/update 042 name Naruto-Uzumaki</code>\n'
            '<code>/update 042 rarity 5</code>\n'
            '<code>/update 042 img_url https://example.com/image.jpg</code>',
            parse_mode='HTML'
        )
        return

    char_id = normalize_character_id(args[0])
    if char_id is None:
        await update.message.reply_text('❌ Character ID must be a number.')
        return

    field, new_value = args[1], args[2]

    valid_fields = ['img_url', 'name', 'anime', 'rarity']
    if field not in valid_fields:
        await update.message.reply_text(
            f'❌ Invalid field. Use one of: <code>{", ".join(valid_fields)}</code>',
            parse_mode='HTML'
        )
        return

    try:
        character = await collection.find_one(character_id_query(char_id))
        if not character:
            await update.message.reply_text(
                f'❌ Character with ID <code>{format_character_id(char_id)}</code> not found.',
                parse_mode='HTML'
            )
            return
        display_char_id = format_character_id(character.get('id', char_id))

        if field in ['name', 'anime']:
            processed_value = new_value.replace('-', ' ').strip().title()
        elif field == 'rarity':
            try:
                rarity_num = int(new_value)
                rarity_level = RarityLevel.get_by_number(rarity_num)
                if not rarity_level:
                    raise ValueError
                processed_value = rarity_level.value[1]
            except ValueError:
                await update.message.reply_text('❌ Rarity must be a number between 1-15.')
                return
        else:
            processed_value = new_value

        await collection.update_one(
            character_id_query(char_id),
            {
                '$set': {
                    field: processed_value,
                    'updated_at': datetime.utcnow(),
                    'updated_by': update.effective_user.id
                }
            }
        )

        if field == 'img_url':
            try:
                if character.get('message_id'):
                    await context.bot.delete_message(
                        chat_id=CHARA_CHANNEL_ID,
                        message_id=character['message_id']
                    )
            except Exception as e:
                logger.warning(f"Could not delete old message: {e}")

            new_msg = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=processed_value,
                caption=(
                    f'<b>🎴 {to_small_caps("Character")}:</b> {character["name"]}\n'
                    f'<b>📺 {to_small_caps("Anime")}:</b> {character["anime"]}\n'
                    f'<b>⭐ {to_small_caps("Rarity")}:</b> {character["rarity"]}\n'
                    f'<b>🆔 {to_small_caps("ID")}:</b> <code>{display_char_id}</code>\n\n'
                    f'<b>✏️ {to_small_caps("Updated by")}:</b> <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>\n'
                    f'<b>🔄 {to_small_caps("Field")}:</b> Image URL'
                ),
                parse_mode='HTML'
            )
            
            await collection.update_one(
                character_id_query(char_id),
                {'$set': {'message_id': new_msg.message_id}}
            )
            
        else:
            try:
                if character.get('message_id'):
                    await context.bot.edit_message_caption(
                        chat_id=CHARA_CHANNEL_ID,
                        message_id=character['message_id'],
                        caption=(
                            f'<b>🎴 {to_small_caps("Character")}:</b> {character["name"] if field != "name" else processed_value}\n'
                            f'<b>📺 {to_small_caps("Anime")}:</b> {character["anime"] if field != "anime" else processed_value}\n'
                            f'<b>⭐ {to_small_caps("Rarity")}:</b> {character["rarity"] if field != "rarity" else processed_value}\n'
                            f'<b>🆔 {to_small_caps("ID")}:</b> <code>{display_char_id}</code>\n\n'
                            f'<b>✏️ {to_small_caps("Updated by")}:</b> <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>\n'
                            f'<b>🔄 {to_small_caps("Field")}:</b> {field}'
                        ),
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.warning(f"Could not edit caption: {e}")

        await update.message.reply_text(
            f'✅ <b>{to_small_caps("Updated Successfully!")}</b>\n\n'
            f'🆔 <b>{to_small_caps("ID")}:</b> <code>{display_char_id}</code>\n'
            f'🔄 <b>{to_small_caps("Field")}:</b> <code>{field}</code>\n'
            f'✨ <b>{to_small_caps("New Value")}:</b> <code>{processed_value[:50]}</code>',
            parse_mode='HTML'
        )
        logger.debug(f"Character {char_id} updated by {update.effective_user.id}: {field} = {processed_value[:30]}")

    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        await update.message.reply_text(f'❌ Error: {str(e)[:200]}')

@admin_only
async def stats(update: Update, context: CallbackContext) -> None:
    """Show database statistics"""
    try:
        total = await collection.count_documents({})
        
        pipeline = [
            {'$group': {'_id': '$rarity', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        rarity_stats = await collection.aggregate(pipeline).to_list(length=None)
        
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent = await collection.count_documents({'created_at': {'$gte': yesterday}})
        
        text = f"📊 <b>{to_small_caps('Database Statistics')}</b>\n\n"
        text += f"📦 <b>{to_small_caps('Total Characters')}:</b> <code>{total}</code>\n"
        text += f"📈 <b>{to_small_caps('Last 24h')}:</b> <code>+{recent}</code>\n\n"
        
        if rarity_stats:
            text += f"<b>⭐ {to_small_caps('Rarity Distribution')}:</b>\n"
            for stat in rarity_stats:
                count = stat['count']
                percentage = (count / total) * 100 if total > 0 else 0
                bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                rarity_name = stat['_id'] if stat['_id'] else "Unknown"
                text += f"{rarity_name}: <code>{count}</code> [{bar}] {percentage:.1f}%\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        logger.debug(f"Stats viewed by {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text(f'❌ Error fetching stats: {str(e)}')

application.add_handler(CommandHandler('upload', upload, block=False))
application.add_handler(CommandHandler('delete', delete, block=False))
application.add_handler(CommandHandler('update', update, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))

logger.info("Admin module loaded successfully")

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
