# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

import re
import time
import asyncio
from cachetools import TTLCache
from pymongo import ASCENDING
import logging

from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
from telegram.ext import InlineQueryHandler, CallbackContext

from senpai import user_collection, collection, application, db
from senpai.media import get_character_image_url
from senpai.utils import to_small_caps, RARITY_MAP

CACHE_TTL_CHARS = 180
CACHE_TTL_USER = 30
CACHE_TTL_COUNT = 120
MAX_RESULTS = 20
COLLECTION_CACHE_TIME = 10
SEARCH_CACHE_TIME = 20

_regex_cache = {}

def get_regex(pattern: str):
    if pattern not in _regex_cache:
        _regex_cache[pattern] = re.compile(re.escape(pattern), re.IGNORECASE)
    return _regex_cache[pattern]

class AsyncCache:
    def __init__(self, ttl: int):
        self.cache = TTLCache(maxsize=10000, ttl=ttl)
        self.locks = {}
    
    async def get(self, key: str, fetch_func):
        if key in self.cache:
            return self.cache[key]
        
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            if key in self.cache:
                return self.cache[key]
            
            value = await fetch_func()
            self.cache[key] = value
            return value

char_cache = AsyncCache(CACHE_TTL_CHARS)
user_cache = AsyncCache(CACHE_TTL_USER)
count_cache = AsyncCache(CACHE_TTL_COUNT)

async def setup_indexes():
    await db.characters.create_index([('id', ASCENDING)], unique=True)
    await db.characters.create_index([('anime', ASCENDING)])
    await db.characters.create_index([('name', ASCENDING)])
    await db.characters.create_index([('rarity', ASCENDING)])
    
    await db.user_collection.create_index([('id', ASCENDING)], unique=True)
    await db.user_collection.create_index([('characters.id', ASCENDING)])
    await db.user_collection.create_index([('characters.anime', ASCENDING)])

async def get_global_character_counts(character_ids: list):
    if not character_ids:
        return {}

    cache_key = f"global_counts:{','.join(sorted(map(str, character_ids)))}"

    async def fetch_counts():
        pipeline = [
            {'$match': {'characters.id': {'$in': character_ids}}},
            {'$unwind': '$characters'},
            {'$match': {'characters.id': {'$in': character_ids}}},
            {'$group': {'_id': '$characters.id', 'count': {'$sum': 1}}},
        ]
        result = await user_collection.aggregate(pipeline).to_list(length=None)
        return {item['_id']: item['count'] for item in result}

    return await count_cache.get(cache_key, fetch_counts)

async def get_anime_totals(anime_names: list):
    if not anime_names:
        return {}

    cache_key = f"anime_totals:{'||'.join(sorted(anime_names))}"

    async def fetch_totals():
        pipeline = [
            {'$match': {'anime': {'$in': anime_names}}},
            {'$group': {'_id': '$anime', 'count': {'$sum': 1}}},
        ]
        result = await collection.aggregate(pipeline).to_list(length=None)
        return {item['_id']: item['count'] for item in result}

    return await count_cache.get(cache_key, fetch_totals)

def get_rarity_display(rarity_val):
    if rarity_val is None:
        return to_small_caps("ɴ/ᴀ")
    
    if isinstance(rarity_val, int):
        return RARITY_MAP.get(rarity_val, to_small_caps(str(rarity_val)))
    
    if isinstance(rarity_val, str):
        if rarity_val.isdigit():
            return RARITY_MAP.get(int(rarity_val), to_small_caps(rarity_val))
        return to_small_caps(rarity_val)
    
    return to_small_caps(str(rarity_val))

async def inlinequery(update: Update, context: CallbackContext) -> None:
    start_time = time.time()
    query = update.inline_query.query or ""
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    cache_time = SEARCH_CACHE_TIME
    is_collection_query = False
    
    try:
        user_id = None
        search_terms = query
        
        if query.startswith('collection.'):
            parts = query.split(' ', 1)
            user_id = int(parts[0].split('.')[1])
            search_terms = parts[1] if len(parts) > 1 else ""
            is_collection_query = True
        elif query and query.split()[0].isdigit():
            parts = query.split(' ', 1)
            user_id = int(parts[0])
            search_terms = parts[1] if len(parts) > 1 else ""
            is_collection_query = True
        
        cache_time = COLLECTION_CACHE_TIME if is_collection_query else SEARCH_CACHE_TIME

        if is_collection_query:
            user = await user_cache.get(
                f"user_{user_id}",
                lambda: user_collection.find_one(
                    {'id': user_id},
                    {'characters': 1, 'first_name': 1, 'id': 1}
                )
            )
            
            if not user or 'characters' not in user:
                await update.inline_query.answer([], cache_time=cache_time, is_personal=True)
                return
            
            seen_ids = set()
            all_characters = []
            char_count_map = {}
            user_anime_count_map = {}
            
            for char in user['characters']:
                cid = char['id']
                anime_name = char.get('anime')
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    all_characters.append(char)
                    char_count_map[cid] = 1
                else:
                    char_count_map[cid] += 1
                if anime_name:
                    user_anime_count_map[anime_name] = user_anime_count_map.get(anime_name, 0) + 1
            
            if search_terms:
                regex = get_regex(search_terms)
                all_characters = [
                    c for c in all_characters 
                    if regex.search(c.get('name', '')) or regex.search(c.get('anime', ''))
                ]
        
        else:
            if search_terms:
                regex = get_regex(search_terms)
                all_characters = await collection.find(
                    {"$or": [{"name": regex}, {"anime": regex}]},
                    {'id': 1, 'name': 1, 'anime': 1, 'img_url': 1, 'tg_file_id': 1, 'rarity': 1}
                ).to_list(length=None)
            else:
                async def fetch_all():
                    return await collection.find(
                        {},
                        {'id': 1, 'name': 1, 'anime': 1, 'img_url': 1, 'tg_file_id': 1, 'rarity': 1}
                    ).to_list(length=None)
                
                all_characters = await char_cache.get('all_chars', fetch_all)
        
        total_count = len(all_characters)
        characters = all_characters[offset:offset + MAX_RESULTS]
        next_offset = str(offset + MAX_RESULTS) if total_count > offset + MAX_RESULTS else ""
        
        if not characters:
            await update.inline_query.answer(
                [],
                next_offset=next_offset,
                cache_time=cache_time,
                is_personal=is_collection_query,
            )
            return
        
        char_ids = [c['id'] for c in characters]
        anime_names = list(set(c['anime'] for c in characters if c.get('anime')))

        if is_collection_query:
            global_counts = {}
            anime_totals = await get_anime_totals(anime_names)
        else:
            global_counts = await get_global_character_counts(char_ids)
            anime_totals = {}
        
        results = []
        for char in characters:
            rarity_val = char.get('rarity')
            rarity_display = get_rarity_display(rarity_val)
            
            if is_collection_query:
                user_char_count = char_count_map.get(char['id'], 1)
                user_anime_count = user_anime_count_map.get(char.get('anime'), 0)
                
                caption = (
                    f"✨ {to_small_caps('look at')} {to_small_caps(user.get('first_name', 'user'))}'s {to_small_caps('character')}\n\n"
                    f"🌸 {to_small_caps('name')} : <b>{to_small_caps(char['name'])} (x{user_char_count})</b>\n"
                    f"🏖️ {to_small_caps('anime')} : <b>{to_small_caps(char['anime'])} ({user_anime_count}/{anime_totals.get(char['anime'], '?')})</b>\n"
                    f"🏵️ {to_small_caps('rarity')} : <b>{rarity_display}</b>\n"
                    f"🆔️ {to_small_caps('id')} : <b>{char['id']}</b>"
                )
            else:
                g_count = global_counts.get(char['id'], 0)
                caption = (
                    f"✨ {to_small_caps('look at this character !!')}\n\n"
                    f"🌸 {to_small_caps('name')} : <b>{to_small_caps(char['name'])}</b>\n"
                    f"🏖️ {to_small_caps('anime')} : <b>{to_small_caps(char['anime'])}</b>\n"
                    f"🏵️ {to_small_caps('rarity')} : <b>{rarity_display}</b>\n"
                    f"🆔️ {to_small_caps('id')} : <b>{char['id']}</b>\n\n"
                    f"{to_small_caps('globally guessed')} {g_count} {to_small_caps('times...')}"
                )
            
            image_url = get_character_image_url(char)
            result_id = f"{'c' if is_collection_query else 's'}_{user_id or 0}_{char['id']}_{offset}"

            if image_url:
                results.append(
                    InlineQueryResultPhoto(
                        id=result_id,
                        photo_url=image_url,
                        thumbnail_url=image_url,
                        caption=caption,
                        parse_mode='HTML'
                    )
                )
            else:
                results.append(
                    InlineQueryResultArticle(
                        id=result_id,
                        title=f"{char['name']} ({char['id']})",
                        description=char.get('anime', ''),
                        input_message_content=InputTextMessageContent(
                            message_text=caption,
                            parse_mode='HTML'
                        )
                    )
                )
        
        elapsed = time.time() - start_time
        logging.debug(f"Inline query processed in {elapsed:.2f}s | Results: {len(results)}")
        
        await update.inline_query.answer(
            results,
            next_offset=next_offset,
            cache_time=cache_time,
            is_personal=is_collection_query,
        )
        
    except Exception as e:
        logging.error(f"Inline query error: {e}", exc_info=True)
        await update.inline_query.answer([], cache_time=COLLECTION_CACHE_TIME, is_personal=True)

application.add_handler(InlineQueryHandler(inlinequery, block=False))

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
