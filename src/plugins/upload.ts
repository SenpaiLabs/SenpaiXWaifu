import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';
import { uploaderCheck, sudoCheck } from '../utils/decorators';
import { languageMiddleware } from '../utils/locales';
import { formatString } from './ping';
import crypto from 'crypto';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('upload', uploaderCheck, languageMiddleware(), async (ctx) => {
        const text = ctx.message.text;
        const tokens = text.split(' ');
        
        if (tokens.length < 5) {
            return await ctx.reply(ctx.lang.upload_1, { parse_mode: 'Markdown' });
        }

        const imgUrl = tokens[1];
        const name = tokens[2].replace(/-/g, ' ');
        const anime = tokens[3].replace(/-/g, ' ');
        const rarityNum = tokens[4];

        const rarityMap: Record<string, string> = {
            "1": "⚪ Common", "2": "🔵 Rare", "3": "🟡 Legendary", "4": "💮 Special",
            "5": "🔮 Limited", "6": "🍭 Kawaii", "7": "🎐 Celestial", "8": "🧬 Cross Version",
            "9": "❄️ Winter", "10": "⛅ Summer", "11": "☔ Rain", "12": "🎃 Halloween",
            "13": "🎄 Christmas", "14": "💝 Valentine", "15": "🪩 Auction", "16": "💸 Premium Edition"
        };

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

            await ctx.telegram.editMessageText(
                ctx.chat.id,
                msg.message_id,
                undefined,
                formatString(ctx.lang.up_3, stdout),
                { parse_mode: 'Markdown' }
            );

            // Restart the process gracefully
            // By exiting with code 0, assuming a process manager like PM2, nodemon, Docker restarts it.
            process.exit(0);

        } catch (e: any) {
            await ctx.telegram.editMessageText(
                ctx.chat.id,
                msg.message_id,
                undefined,
                formatString(ctx.lang.up_4, e.toString()),
                { parse_mode: 'Markdown' }
            );
        }
    });
}
