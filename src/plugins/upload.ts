import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';
import { uploaderCheck, sudoCheck } from '../utils/decorators';
import { languageMiddleware } from '../utils/locales';
import { formatString } from './ping';
import crypto from 'crypto';
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { pipeline } from 'stream/promises';

const execPromise = util.promisify(exec);

const rarityMap: Record<string, string> = {
    "1": "⚪ Common", "2": "🔵 Rare", "3": "🟡 Legendary", "4": "💮 Special",
    "5": "🔮 Limited", "6": "🍭 Kawaii", "7": "🎐 Celestial", "8": "🧬 Cross Version",
    "9": "❄️ Winter", "10": "⛅ Summer", "11": "☔ Rain", "12": "🎃 Halloween",
    "13": "🎄 Christmas", "14": "💝 Valentine", "15": "🪩 Auction", "16": "💸 Premium Edition"
};

async function uploadToImgbb(ctx: any, photoElement: any): Promise<string | null> {
    try {
        const fileLink = await ctx.telegram.getFileLink(photoElement.file_id);
        const response = await fetch(fileLink.href);
        if (!response.ok || !response.body) return null;

        const tempFileName = crypto.randomUUID() + '.jpg';
        const localPath = path.join(process.cwd(), tempFileName);
        const fileStream = fs.createWriteStream(localPath);
        await pipeline(response.body as any, fileStream);

        const apiKey = "c80e46893d6143f407e66fa944f0c46c";
        const formData = new FormData();
        const fileBuffer = fs.readFileSync(localPath);
        const blob = new Blob([fileBuffer], { type: 'image/jpeg' });
        formData.append('image', blob, tempFileName);

        const uploadResponse = await fetch(`https://api.imgbb.com/1/upload?key=${apiKey}`, {
            method: 'POST',
            body: formData,
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        });

        const res = await uploadResponse.json() as any;
        if (fs.existsSync(localPath)) fs.unlinkSync(localPath);
        
        return res.success ? res.data.url : null;
    } catch (e) {
        return null;
    }
}

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('upload', uploaderCheck, languageMiddleware(), async (ctx) => {
        const message = ctx.message as any;
        const text = message.text || message.caption || "";
        
        const lines = text.split('\n').map((line: string) => line.trim()).filter((line: string) => line.length > 0);
        
        if (lines[0].startsWith('/upload')) {
            lines.shift();
        }

        let imgUrl = "";
        let name = "";
        let anime = "";
        let rarityNum = "";

        const photoArr = message.photo || message.reply_to_message?.photo;
        
        if (photoArr && photoArr.length > 0) {
            if (lines.length < 3) {
                return await ctx.reply(ctx.lang.upload_1, { parse_mode: 'HTML' });
            }
            name = lines[0];
            anime = lines[1];
            rarityNum = lines[2];

            const msg = await ctx.reply(ctx.lang.tgm_downloading);
            const highestRes = photoArr[photoArr.length - 1];
            const uploadedUrl = await uploadToImgbb(ctx, highestRes);
            
            if (!uploadedUrl) {
                return await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, ctx.lang.tgm_download_fail);
            }
            imgUrl = uploadedUrl;
            await ctx.telegram.deleteMessage(ctx.chat.id, msg.message_id).catch(() => {});
            
        } else {
            if (lines.length < 4) {
                return await ctx.reply(ctx.lang.upload_1, { parse_mode: 'HTML' });
            }
            imgUrl = lines[0];
            name = lines[1];
            anime = lines[2];
            rarityNum = lines[3];
        }

        const rarity = rarityMap[rarityNum] || "⚪ Common";

        const character = {
            id: crypto.randomUUID(),
            img_url: imgUrl,
            name: name,
            anime: anime,
            rarity: rarity
        };

        await mongodb.characters.insertOne(character);
        await ctx.reply(formatString(ctx.lang.char_uploaded, name), { parse_mode: 'Markdown' });
    });

    bot.command(['del', 'delete'], uploaderCheck, languageMiddleware(), async (ctx) => {
        const text = ctx.message.text;
        const tokens = text.split(' ');

        if (tokens.length < 2) {
            return await ctx.reply(ctx.lang.upload_2, { parse_mode: 'Markdown' });
        }

        const charId = tokens[1];
        const result = await mongodb.deleteCharacter(charId);
        if (result.deletedCount > 0) {
            await ctx.reply(formatString(ctx.lang.char_deleted, charId), { parse_mode: 'Markdown' });
        } else {
            await ctx.reply(ctx.lang.char_delete_fail);
        }
    });

    bot.command('update', sudoCheck, languageMiddleware(), async (ctx) => {
        const msg = await ctx.reply(ctx.lang.up_1);
        try {
            const { stdout } = await execPromise("git pull origin master");
            if (stdout.includes("Already up to date.")) {
                return await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, ctx.lang.up_2);
            }
            await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formatString(ctx.lang.up_3, stdout), { parse_mode: 'Markdown' });
            process.exit(0);
        } catch (e: any) {
            await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formatString(ctx.lang.up_4, e.toString()), { parse_mode: 'Markdown' });
        }
    });
}
