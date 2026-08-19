import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.on('inline_query', languageMiddleware(), async (ctx) => {
        const query = ctx.inlineQuery.query;

        const results = [
            {
                type: 'article',
                id: '1',
                title: ctx.lang.iquery_1,
                description: ctx.lang.iquery_2,
                input_message_content: {
                    message_text: ctx.lang.iquery_2
                }
            }
        ];

        await ctx.answerInlineQuery(results as any, { cache_time: 1 });
    });
}
