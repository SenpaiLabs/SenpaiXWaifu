import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { mongodb } from '../core/mongo';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command(['top', 'leaderboard'], async (ctx) => {
        const users = await mongodb.users.find({}).toArray();
        if (!users || users.length === 0) {
            return await ctx.reply(ctx.lang.leaderboard_1);
        }
        
        // Sort users by number of characters
        users.sort((a, b) => {
            const aLen = a.characters?.length || 0;
            const bLen = b.characters?.length || 0;
            return bLen - aLen;
        });
        
        let text = ctx.lang.leaderboard_2;
        for (let i = 0; i < Math.min(10, users.length); i++) {
            const user = users[i];
            const name = user.first_name || user.name || ctx.lang.leaderboard_3;
            const charCount = user.characters?.length || 0;
            text += `${i + 1}. ${name} - ${charCount} ${ctx.lang.leaderboard_4}\n`;
        }
        
        await ctx.reply(text, { parse_mode: 'HTML' });
    });
}
