import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';
import { sudoCheck } from '../utils/decorators';
import { languageMiddleware } from '../utils/locales';
import { formatString } from './ping';
import pLimit from 'p-limit';

async function delay(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function broadcastToTarget(
    chatId: number,
    sent: { count: number },
    failed: { count: number },
    bot: Telegraf<SenpaiContext>,
    fromChatId: number,
    messageId: number
) {
    try {
        await bot.telegram.copyMessage(chatId, fromChatId, messageId);
        sent.count++;
        await delay(100);
    } catch (e: any) {
        if (e.code === 429) { // Flood wait
            const retryAfter = e.parameters?.retry_after || 1;
            await delay((retryAfter + 1) * 1000);
            try {
                await bot.telegram.copyMessage(chatId, fromChatId, messageId);
                sent.count++;
            } catch (err) {
                failed.count++;
            }
        } else {
            failed.count++;
        }
    }
}

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('broadcast', sudoCheck, languageMiddleware(), async (ctx) => {
        const message = ctx.message as any;
        if (!message || !message.reply_to_message) {
            return await ctx.reply(ctx.lang.broad_1);
        }

        const users = await mongodb.users.find({}).toArray();
        const groups = await mongodb.chats.find({}).toArray();

        const totalUsers = users.length;
        const totalGroups = groups.length;

        const msg = await ctx.reply(
            formatString(ctx.lang.broad_2, totalUsers, totalGroups)
        );

        const fromChatId = message.chat.id;
        const messageId = message.reply_to_message.message_id;
        const limit = pLimit(5);

        // User Broadcast
        const sentUsers = { count: 0 };
        const failedUsers = { count: 0 };
        const userIds = users.map(u => u.id);
        
        await Promise.all(userIds.map(id => 
            limit(() => broadcastToTarget(id, sentUsers, failedUsers, bot, fromChatId, messageId))
        ));

        // Group Broadcast
        const sentGroups = { count: 0 };
        const failedGroups = { count: 0 };
        const groupIds = groups.map(g => g.id);

        await Promise.all(groupIds.map(id => 
            limit(() => broadcastToTarget(id, sentGroups, failedGroups, bot, fromChatId, messageId))
        ));

        await ctx.telegram.editMessageText(
            ctx.chat.id,
            msg.message_id,
            undefined,
            formatString(ctx.lang.broad_3, sentUsers.count, sentGroups.count)
        );
    });
}
