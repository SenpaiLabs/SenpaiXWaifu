import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { mongodb } from '../core/mongo';
import { formatString } from './ping';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command(['harem', 'collection'], languageMiddleware(), async (ctx) => {
        const userId = ctx.from?.id;
        if (!userId) return;

        const user = await mongodb.getUser(userId);

        if (!user || !user.characters || user.characters.length === 0) {
            return await ctx.reply(ctx.lang.harem_empty);
        }

        const characters = user.characters;
        let text = formatString(ctx.lang.harem_header, user.first_name || user.username || 'User');

        for (let i = 0; i < Math.min(15, characters.length); i++) {
            const chara = characters[i];
            text += `${i + 1}. **${chara.name}** (${chara.rarity})\n`;
        }

        if (characters.length > 15) {
            text += formatString(ctx.lang.harem_footer, characters.length - 15);
        }

        await ctx.reply(text, { parse_mode: 'Markdown' });
    });
}
