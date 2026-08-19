import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { startMarkup, helpMarkup } from '../utils/inline';
import { formatString } from './ping';
import { config } from '../config';
import { mongodb } from '../core/mongo';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('start', languageMiddleware(), async (ctx) => {
        const isPrivate = ctx.chat.type === 'private';
        const botName = ctx.botInfo.first_name;

        const text = isPrivate
            ? formatString(ctx.lang.start_pm, ctx.from.first_name, botName)
            : formatString(ctx.lang.start_gp, botName);

        if (ctx.from) {
            await mongodb.updateUser(ctx.from.id, {
                id: ctx.from.id,
                name: ctx.from.first_name,
                username: ctx.from.username
            });
        }

        const markup = startMarkup(ctx.lang, isPrivate);

        await ctx.replyWithPhoto(
            { url: config.START_IMG.startsWith('http') ? config.START_IMG : undefined, source: !config.START_IMG.startsWith('http') ? config.START_IMG : undefined } as any,
            {
                caption: text,
                reply_markup: markup.reply_markup,
                parse_mode: 'Markdown'
            }
        );
    });

    bot.action('help_menu', languageMiddleware(), async (ctx) => {
        await ctx.editMessageCaption(
            ctx.lang.help_menu,
            {
                reply_markup: helpMarkup(ctx.lang).reply_markup,
                parse_mode: 'Markdown'
            }
        );
    });

    bot.action('start_menu', languageMiddleware(), async (ctx) => {
        const botName = ctx.botInfo.first_name;
        const text = formatString(
            ctx.lang.start_pm,
            ctx.from?.first_name || "User",
            botName
        );

        await ctx.editMessageCaption(
            text,
            {
                reply_markup: startMarkup(ctx.lang, true).reply_markup,
                parse_mode: 'Markdown'
            }
        );
    });
}
