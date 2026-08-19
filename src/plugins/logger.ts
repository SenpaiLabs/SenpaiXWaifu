import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';
import { languageMiddleware } from '../utils/locales';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.on('new_chat_members', languageMiddleware(), async (ctx) => {
        const newMembers = ctx.message.new_chat_members;
        const botId = ctx.botInfo.id;
        
        for (const member of newMembers) {
            if (member.id === botId) {
                // Bot was added to a group
                const chatId = ctx.chat.id;
                let title = ctx.lang.logger_1;
                if ('title' in ctx.chat) {
                    title = ctx.chat.title;
                }
                
                // Add to DB
                await mongodb.addChat(chatId, title);
            }
        }
    });

    bot.on('left_chat_member', languageMiddleware(), async (ctx) => {
        const leftMember = ctx.message.left_chat_member;
        const botId = ctx.botInfo.id;

        if (leftMember.id === botId) {
            // Bot was removed from the group
            const chatId = ctx.chat.id;
            await mongodb.removeChat(chatId);
        }
    });
}
