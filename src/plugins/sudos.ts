import { Telegraf } from 'telegraf';
import { SenpaiContext, senpai } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { ownerCheck, sudoCheck } from '../utils/decorators';
import { extractUser } from '../utils/extract';
import { mongodb } from '../core/mongo';
import { formatString } from './ping';
import { User } from 'telegraf/typings/core/types/typegram';

function getMention(user: User): string {
    return `[${user.first_name || 'User'}](tg://user?id=${user.id})`;
}

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command(['addsudo', 'delsudo', 'rmsudo'], ownerCheck, languageMiddleware(), async (ctx) => {
        const user = await extractUser(ctx);
        if (!user) {
            return await ctx.reply(ctx.lang.user_not_found);
        }

        const cmd = ctx.message.text.split(' ')[0].replace('/', '').split('@')[0];

        if (cmd === 'addsudo') {
            if (senpai.sudoers.has(user.id)) {
                return await ctx.reply(formatString(ctx.lang.sudo_already, getMention(user)), { parse_mode: 'Markdown' });
            }

            senpai.sudoers.add(user.id);
            await mongodb.addSudo(user.id);
            await ctx.reply(formatString(ctx.lang.sudo_added, getMention(user)), { parse_mode: 'Markdown' });

        } else {
            if (!senpai.sudoers.has(user.id)) {
                return await ctx.reply(formatString(ctx.lang.sudo_not, getMention(user)), { parse_mode: 'Markdown' });
            }

            if (user.id === senpai.owner) {
                return await ctx.reply(ctx.lang.sudos_err_owner);
            }

            senpai.sudoers.delete(user.id);
            await mongodb.delSudo(user.id);
            await ctx.reply(formatString(ctx.lang.sudo_removed, getMention(user)), { parse_mode: 'Markdown' });
        }
    });

    bot.command(['listsudo', 'sudolist'], languageMiddleware(), async (ctx) => {
        const sent = await ctx.reply(ctx.lang.sudo_fetching);

        let oMention = `Owner (${senpai.owner})`;
        try {
            const ownerObj = await ctx.telegram.getChat(senpai.owner) as any;
            if (ownerObj) {
                oMention = `[${ownerObj.first_name || ownerObj.title || 'Owner'}](tg://user?id=${senpai.owner})`;
            }
        } catch (e) {}

        let txt = formatString(ctx.lang.sudo_owner, oMention);
        txt += ctx.lang.sudo_users + "\n";
        const sudoers = await mongodb.getSudoers();
        if (sudoers && sudoers.length > 0) {
            txt += ctx.lang.sudo_users;
        }

        for (const userId of sudoers) {
            if (userId === senpai.owner) continue;
            try {
                const userObj = await ctx.telegram.getChat(userId) as any;
                const userMention = `[${userObj.first_name || userObj.title || 'User'}](tg://user?id=${userId})`;
                txt += `\n- ${userMention}`;
            } catch (e) {
                txt += `\n- \`${userId}\``;
            }
        }

        await ctx.telegram.editMessageText(ctx.chat.id, sent.message_id, undefined, txt, { parse_mode: 'Markdown' });
    });

    bot.command(['adduploader', 'deluploader', 'rmuploader'], sudoCheck, languageMiddleware(), async (ctx) => {
        const user = await extractUser(ctx);
        if (!user) {
            return await ctx.reply(ctx.lang.user_not_found);
        }

        const cmd = ctx.message.text.split(' ')[0].replace('/', '').split('@')[0];

        if (cmd === 'adduploader') {
            if (senpai.uploaders.has(user.id)) {
                return await ctx.reply(formatString(ctx.lang.uploader_already, getMention(user)), { parse_mode: 'Markdown' });
            }

            senpai.uploaders.add(user.id);
            await mongodb.addUploader(user.id);
            await ctx.reply(formatString(ctx.lang.uploader_added, getMention(user)), { parse_mode: 'Markdown' });

        } else {
            if (!senpai.uploaders.has(user.id)) {
                return await ctx.reply(formatString(ctx.lang.uploader_not, getMention(user)), { parse_mode: 'Markdown' });
            }

            if (user.id === senpai.owner || senpai.sudoers.has(user.id)) {
                return await ctx.reply(ctx.lang.err_1);
            }

            senpai.uploaders.delete(user.id);
            await mongodb.delUploader(user.id);
            await ctx.reply(formatString(ctx.lang.uploader_removed, getMention(user)), { parse_mode: 'Markdown' });
        }
    });

    bot.command(['listuploader', 'uploaderlist'], sudoCheck, languageMiddleware(), async (ctx) => {
        const sent = await ctx.reply(ctx.lang.uploader_fetching);

        const uploaders = await mongodb.getUploaders();
        if (!uploaders || uploaders.length === 0) {
            return await ctx.telegram.editMessageText(ctx.chat.id, sent.message_id, undefined, ctx.lang.err_2);
        }

        let txt = ctx.lang.uploader_users + "\n";

        for (const userId of uploaders) {
            try {
                const userObj = await ctx.telegram.getChat(userId) as any;
                const userMention = `[${userObj.first_name || userObj.title || 'User'}](tg://user?id=${userId})`;
                txt += `\n- ${userMention}`;
            } catch (e) {
                txt += `\n- \`${userId}\``;
            }
        }

        await ctx.telegram.editMessageText(ctx.chat.id, sent.message_id, undefined, txt, { parse_mode: 'Markdown' });
    });
}
