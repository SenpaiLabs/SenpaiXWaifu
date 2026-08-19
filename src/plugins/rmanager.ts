import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';
import { sudoCheck } from '../utils/decorators';
import { formatString } from './ping';
import { languageMiddleware } from '../utils/locales';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('set_on', sudoCheck, languageMiddleware(), async (ctx) => {
        const text = ctx.message.text;
        const tokens = text.split(' ');
        if (tokens.length < 2) {
            return await ctx.reply(ctx.lang.rmanager_1, { parse_mode: 'Markdown' });
        }

        const rarityNum = tokens[1];

        if (rarityNum === "15" || rarityNum === "16") {
            return await ctx.reply(ctx.lang.rmanager_2);
        }

        const allRarities = await mongodb.getAllRarities();
        if (!allRarities.some(r => r.id === rarityNum)) {
            return await ctx.reply(ctx.lang.rmanager_3);
        }

        const success = await mongodb.setRarityStatus(rarityNum, true);
        if (success) {
            const activeRarities = await mongodb.getActiveRarities();
            const rarityNames = activeRarities.map(r => `${r.emoji} ${r.name} (${r.base_percent}%)`).join("\n");
            const replyText = formatString(ctx.lang.rmanager_4, rarityNames);
            await ctx.reply(replyText, { parse_mode: 'Markdown' });
        } else {
            await ctx.reply(ctx.lang.rmanager_5);
        }
    });

    bot.command('set_off', sudoCheck, languageMiddleware(), async (ctx) => {
        const text = ctx.message.text;
        const tokens = text.split(' ');
        if (tokens.length < 2) {
            return await ctx.reply(ctx.lang.rmanager_6, { parse_mode: 'Markdown' });
        }

        const rarityNum = tokens[1];

        const allRarities = await mongodb.getAllRarities();
        if (!allRarities.some(r => r.id === rarityNum)) {
            return await ctx.reply(ctx.lang.rmanager_7);
        }

        const success = await mongodb.setRarityStatus(rarityNum, false);
        if (success) {
            const updatedSettings = await mongodb.getActiveRarities();
            let replyText = "";
            if (updatedSettings.length === 0) {
                replyText = ctx.lang.rmanager_8;
            } else {
                const rarityNames = updatedSettings.map(s => s.name).join(', ');
                replyText = formatString(ctx.lang.rmanager_9, rarityNames);
            }
            await ctx.reply(replyText, { parse_mode: 'Markdown' });
        } else {
            await ctx.reply(ctx.lang.rmanager_5);
        }
    });
}
