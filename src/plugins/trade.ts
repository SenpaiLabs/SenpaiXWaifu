import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('trade', languageMiddleware(), async (ctx) => {
        const message = ctx.message as any;
        if (!message || !message.reply_to_message) {
            return await ctx.reply(ctx.lang.trade_1);
        }
        
        await ctx.reply(ctx.lang.trade_2); // Kept exact string as instructed
    });
}
