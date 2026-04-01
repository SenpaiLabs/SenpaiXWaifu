# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

"""
Centralized utility module for SenpaiWaifuBot.
All small caps conversion, rarity maps, and shared helpers live here.
Import from senpai.utils instead of duplicating in every module.
"""

# ==================== SMALL CAPS ====================

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
    'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
    'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ',
    'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ',
    'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ',
    'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ',
    'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ',
    'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ',
    'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ',
    'Z': 'ᴢ',
    ' ': ' ', '-': '-', '/': '/', '(': '(', ')': ')',
    '[': '[', ']': ']', '{': '{', '}': '}', ':': ':',
    '.': '.', ',': ',', '!': '!', '?': '?', "'": "'",
    '"': '"', '&': '&', '@': '@', '#': '#', '$': '$',
    '%': '%', '^': '^', '*': '*', '+': '+', '=': '=',
    '_': '_', '|': '|', '\\': '\\', '`': '`', '~': '~',
    '<': '<', '>': '>', ';': ';', '\n': '\n',
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
}


def to_small_caps(text: str) -> str:
    """Convert standard text to Small Caps Unicode characters."""
    return ''.join(SMALL_CAPS_MAP.get(c, c) for c in str(text))


# Alias — some modules use `small_caps` instead of `to_small_caps`
small_caps = to_small_caps


# ==================== RARITY SYSTEM ====================

RARITY_EMOJIS = {
    1: '⚪', 2: '🔵', 3: '🟡', 4: '💮', 5: '👹',
    6: '🎐', 7: '🔮', 8: '🪐', 9: '⚰️', 10: '🌬️',
    11: '💝', 12: '🌸', 13: '🏖️', 14: '🍭', 15: '🧬',
}

RARITY_NAMES = {
    1: "ᴄᴏᴍᴍᴏɴ",     2: "ʀᴀʀᴇ",        3: "ʟᴇɢᴇɴᴅᴀʀʏ",
    4: "ꜱᴘᴇᴄɪᴀʟ",    5: "ᴀɴᴄɪᴇɴᴛ",     6: "ᴄᴇʟᴇꜱᴛɪᴀʟ",
    7: "ᴇᴘɪᴄ",       8: "ᴄᴏꜱᴍɪᴄ",      9: "ɴɪɢʜᴛᴍᴀʀᴇ",
    10: "ꜰʀᴏꜱᴛʙᴏʀɴ", 11: "ᴠᴀʟᴇɴᴛɪɴᴇ",  12: "ꜱᴘʀɪɴɢ",
    13: "ᴛʀᴏᴘɪᴄᴀʟ",  14: "ᴋᴀᴡᴀɪɪ",     15: "ʜʏʙʀɪᴅ",
}

# Combined map: {1: "⚪ ᴄᴏᴍᴍᴏɴ", 2: "🔵 ʀᴀʀᴇ", ...}
RARITY_MAP = {
    k: f"{RARITY_EMOJIS[k]} {RARITY_NAMES[k]}"
    for k in RARITY_EMOJIS
}

# Reverse lookup: {"⚪ ᴄᴏᴍᴍᴏɴ": 1, "🔵 ʀᴀʀᴇ": 2, ...}
RARITY_TEXT_TO_NUMBER = {v: k for k, v in RARITY_MAP.items()}


def get_rarity_display(rarity: int) -> str:
    """Return formatted rarity string like '⚪ ᴄᴏᴍᴍᴏɴ'."""
    return RARITY_MAP.get(rarity, f"⚪ ᴜɴᴋɴᴏᴡɴ ({rarity})")


def get_rarity_emoji(rarity: int) -> str:
    """Return just the emoji for a rarity tier."""
    return RARITY_EMOJIS.get(rarity, '⚪')


def get_rarity_name(rarity: int) -> str:
    """Return just the small-caps name for a rarity tier."""
    return RARITY_NAMES.get(rarity, 'ᴜɴᴋɴᴏᴡɴ')


def get_rarity_from_string(rarity_value) -> int:
    """
    Parse rarity from various formats:
      - int: 1-15
      - str digit: "3"
      - emoji: "🟡"
      - name: "legendary"
      - combined: "🟡 ʟᴇɢᴇɴᴅᴀʀʏ"
    Returns int rarity (default 1 if unknown).
    """
    if isinstance(rarity_value, int):
        return rarity_value

    if isinstance(rarity_value, str):
        rarity_str = rarity_value.strip()

        if rarity_str.isdigit():
            return int(rarity_str)

        # Check emoji
        for num, emoji in RARITY_EMOJIS.items():
            if emoji in rarity_str:
                return num

        # Check English name (case-insensitive)
        name_to_int = {
            'common': 1, 'rare': 2, 'legendary': 3, 'special': 4,
            'ancient': 5, 'celestial': 6, 'epic': 7, 'cosmic': 8,
            'nightmare': 9, 'frostborn': 10, 'valentine': 11,
            'spring': 12, 'tropical': 13, 'kawaii': 14, 'hybrid': 15,
        }
        lower = rarity_str.lower()
        if lower in name_to_int:
            return name_to_int[lower]

    return 1

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
