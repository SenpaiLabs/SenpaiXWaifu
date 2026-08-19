import { SenpaiContext, senpai } from '../core/bot';

export async function sudoCheck(ctx: SenpaiContext, next: () => Promise<void>) {
    const userId = ctx.from?.id;
    if (!userId) return;

    if (userId !== senpai.owner && !senpai.sudoers.has(userId)) {
        const text = ctx.lang?.sudo_only || "You must be a sudo user to use this command.";
        if (ctx.updateType === 'callback_query') {
            await ctx.answerCbQuery(text, { show_alert: true });
        } else {
            await ctx.reply(text);
        }
        return;
    }
    return next();
}

export async function uploaderCheck(ctx: SenpaiContext, next: () => Promise<void>) {
    const userId = ctx.from?.id;
    if (!userId) return;

    if (userId !== senpai.owner && !senpai.sudoers.has(userId) && !senpai.uploaders.has(userId)) {
        const text = ctx.lang?.uploader_only || "You are not an uploader!";
        if (ctx.updateType === 'callback_query') {
            await ctx.answerCbQuery(text, { show_alert: true });
        } else {
            await ctx.reply(text);
        }
        return;
    }
    return next();
}

export async function adminCheck(ctx: SenpaiContext, next: () => Promise<void>) {
    const chat = ctx.chat;
    if (!chat) return;

    if (chat.type === 'private') {
        return next();
    }

    const userId = ctx.from?.id;
    if (!userId) return;

    if (userId === senpai.owner || senpai.sudoers.has(userId)) {
        return next();
    }

    try {
        const member = await ctx.telegram.getChatMember(chat.id, userId);
        if (member.status === 'administrator' || member.status === 'creator') {
            return next();
        }
    } catch (err) {
        // Fallthrough on error
    }

    const text = ctx.lang?.admin_only || "You must be an admin!";
    if (ctx.updateType === 'callback_query') {
        await ctx.answerCbQuery(text, { show_alert: true });
    } else {
        await ctx.reply(text);
    }
    return;
}

export async function ownerCheck(ctx: SenpaiContext, next: () => Promise<void>) {
    const userId = ctx.from?.id;
    if (!userId) return;

    if (userId !== senpai.owner) {
        const text = "Only the bot owner can use this command.";
        if (ctx.updateType === 'callback_query') {
            await ctx.answerCbQuery(text, { show_alert: true });
        } else {
            await ctx.reply(text);
        }
        return;
    }
    return next();
}
