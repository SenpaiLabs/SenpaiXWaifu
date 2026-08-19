import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { sudoCheck } from '../utils/decorators';
import { languageMiddleware } from '../utils/locales';
import { formatString } from './ping';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('changetime', sudoCheck, languageMiddleware(), async (ctx) => {
        const text = ctx.message.text;
        const tokens = text.split(' ');

        if (tokens.length < 2) {
            return await ctx.reply(ctx.lang.change_1);
        }

        try {
            const newFrequency = parseInt(tokens[1]);
            if (isNaN(newFrequency)) {
                return await ctx.reply(ctx.lang.change_4);
            }
            if (newFrequency < 10) {
                return await ctx.reply(ctx.lang.change_2);
            }

            // Example DB update:
            // await db.user_totals_collection.update_one({'chat_id': str(chat_id)}, {'$set': {'message_frequency': new_frequency}}, upsert=True)
            
            await ctx.reply(formatString(ctx.lang.change_3, newFrequency));
        } catch (e) {
            await ctx.reply(ctx.lang.change_4);
        }
    });
}
