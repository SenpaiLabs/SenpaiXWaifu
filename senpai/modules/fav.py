# (c) @SenpaiLabs
# SenpaiLabs Developer

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from senpai import application, user_collection, LOGGER
from senpai.character_ids import character_matches_id, normalize_character_id
from senpai.utils import to_small_caps


async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text(to_small_caps("Please provide a character ID: /fav <id>"))
        return

    try:
        character_id = int(args[0])
    except ValueError:
        await update.message.reply_text(to_small_caps("Character ID must be a number."))
        return

    try:
        user = await user_collection.find_one({'id': user_id})
    except Exception:
        LOGGER.exception("Failed to fetch user for fav")
        user = None

    if not user or not user.get('characters'):
        await update.message.reply_text(to_small_caps("You have not collected any characters yet."))
        return

    character = next((c for c in user['characters'] if character_matches_id(c, character_id)), None)
    if not character:
        await update.message.reply_text(to_small_caps("That character is not in your collection."))
        return

    try:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'favorites': [character_id]}}
        )
        await update.message.reply_text(
            to_small_caps(f"Character {character.get('name')} has been added to your favorites.")
        )
    except Exception:
        LOGGER.exception("Failed to set favorite character")
        await update.message.reply_text(to_small_caps("Failed to mark favorite. Please try again later."))


async def unfav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    args = context.args or []
    if not args:
        await update.message.reply_text(to_small_caps("Please provide a character ID: /unfav <id>"))
        return

    try:
        character_id = int(args[0])
    except ValueError:
        await update.message.reply_text(to_small_caps("Character ID must be a number."))
        return

    try:
        user = await user_collection.find_one({'id': user_id})
    except Exception:
        LOGGER.exception("Failed to fetch user for unfav")
        user = None

    if not user or not user.get('characters'):
        await update.message.reply_text(to_small_caps("You have not collected any characters yet."))
        return

    favorites = user.get('favorites', [])
    updated_favorites = [
        favorite for favorite in favorites
        if normalize_character_id(favorite) != character_id
    ]

    if len(updated_favorites) == len(favorites):
        await update.message.reply_text(to_small_caps("That character is not in your favorites."))
        return

    try:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'favorites': updated_favorites}}
        )
        await update.message.reply_text(
            to_small_caps(f"Character ID {character_id} has been removed from your favorites.")
        )
    except Exception:
        LOGGER.exception("Failed to remove favorite character")
        await update.message.reply_text(to_small_caps("Failed to remove favorite. Please try again later."))


application.add_handler(CommandHandler("fav", fav, block=False))
application.add_handler(CommandHandler("unfav", unfav, block=False))
