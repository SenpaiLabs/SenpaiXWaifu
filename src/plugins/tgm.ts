import { Telegraf, Markup } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { formatString } from './ping';
import fs from 'fs';
import path from 'path';
import { pipeline } from 'stream/promises';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command(['tgm', 'imgbb'], languageMiddleware(), async (ctx) => {
        const message = ctx.message as any;
        if (!message || !message.reply_to_message || !message.reply_to_message.photo) {
            return await ctx.reply(ctx.lang.tgm_reply_media);
        }

        const msg = await ctx.reply(ctx.lang.tgm_downloading);

        const photos = message.reply_to_message.photo;
        const highestRes = photos[photos.length - 1];

        let localPath = '';

        try {
            const fileLink = await ctx.telegram.getFileLink(highestRes.file_id);
            const response = await fetch(fileLink.href);

            if (!response.ok || !response.body) {
                return await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, ctx.lang.tgm_download_fail);
            }

            localPath = path.join(process.cwd(), 'abc.jpg');
            if (fs.existsSync(localPath)) {
                fs.unlinkSync(localPath);
            }

            const fileStream = fs.createWriteStream(localPath);
            await pipeline(response.body as any, fileStream);

        } catch (e) {
            return await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, ctx.lang.tgm_download_fail);
        }

        await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formatString(ctx.lang.tgm_uploading, "IMGBB"));

        try {
            const apiKey = "c80e46893d6143f407e66fa944f0c46c";
            
            const formData = new FormData();
            const fileBuffer = fs.readFileSync(localPath);
            const blob = new Blob([fileBuffer], { type: 'image/jpeg' });
            formData.append('image', blob, 'abc.jpg');

            const uploadResponse = await fetch(`https://api.imgbb.com/1/upload?key=${apiKey}`, {
                method: 'POST',
                body: formData,
                headers: {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                }
            });

            const res = await uploadResponse.json() as any;

            if (res.success) {
                const url = res.data.url;
                const markup = Markup.inlineKeyboard([
                    [Markup.button.url("🔗 Open Link", url)]
                ]);
                await ctx.telegram.editMessageText(
                    ctx.chat.id,
                    msg.message_id,
                    undefined,
                    formatString(ctx.lang.tgm_success, url),
                    {
                        parse_mode: 'Markdown',
                        reply_markup: markup.reply_markup,
                        disable_web_page_preview: true
                    } as any
                );
            } else {
                const errorMsg = res.error?.message || "Unknown error";
                await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formatString(ctx.lang.tgm_imgbb_err, errorMsg));
            }
        } catch (e: any) {
            await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formatString(ctx.lang.tgm_err, e.toString()));
        } finally {
            if (fs.existsSync(localPath)) {
                fs.unlinkSync(localPath);
            }
        }
    });
}
