import { SenpaiContext } from '../core/bot';
import { User } from 'telegraf/typings/core/types/typegram';

export async function extractUser(ctx: SenpaiContext): Promise<User | null> {
    const message = ctx.message as any;
    if (!message) return null;

    if (!message.reply_to_message) {
        if (!message.text) return null;
        const tokens = message.text.split(' ');
        if (tokens.length < 2) return null;

        let userIdStr = tokens[1];
        if (userIdStr.startsWith('@')) {
            userIdStr = userIdStr.substring(1);
        }

        try {
            // Telegraf has no direct get_users equivalent.
            // getChat works for both IDs and usernames, but returns Chat, not User.
            // So we cast it/extract user info if available.
            const chat = await ctx.telegram.getChat(userIdStr) as any;
            if (chat) {
                return {
                    id: chat.id,
                    is_bot: false,
                    first_name: chat.first_name || chat.title || 'Unknown',
                    username: chat.username
                } as User;
            }
        } catch (err) {
            return null;
        }
        return null;
    } else {
        return message.reply_to_message.from || null;
    }
}
