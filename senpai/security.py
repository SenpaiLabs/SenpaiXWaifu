# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs

from senpai.config import Config


def is_owner(user_id: int) -> bool:
    return isinstance(user_id, int) and user_id == Config.OWNER_ID


def is_owner_or_sudo(user_id: int) -> bool:
    return isinstance(user_id, int) and (is_owner(user_id) or user_id in Config.SUDO_USERS)


def can_use_eval(user_id: int) -> bool:
    return isinstance(user_id, int) and user_id in Config.EVAL_USERS

# (c) @SenpaiLabs
# SenpaiLabs Developer 
# Don't Remove Credit 😔
# Telegram Channel @Senpai_Updates & @THE_DRAGON_SUPPORT
# Developer @SenpaiLabs
