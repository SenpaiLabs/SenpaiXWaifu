import { Telegraf, Markup } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { mongodb, Character, Rarity } from '../core/mongo';
import { formatString } from './ping';

export const messageCounts: Record<number, number> = {};
const sentCharacters: Record<number, string[]> = {};
const lastCharacters: Record<number, Character> = {};
const firstCorrectGuesses: Record<number, number> = {};

function weightedRandom(population: any[], weights: number[]): any {
    const totalWeight = weights.reduce((sum, w) => sum + w, 0);
    const rand = Math.random() * totalWeight;
    let sum = 0;
    for (let i = 0; i < population.length; i++) {
        sum += weights[i];
        if (rand < sum) {
            return population[i];
        }
    }
    return population[0];
}

async function sendImage(bot: Telegraf<SenpaiContext>, ctx: SenpaiContext, chatId: number) {
    const activeRarities = await mongodb.getActiveRarities();
    if (!activeRarities || activeRarities.length === 0) return;

    const population = activeRarities.map(r => r.name);
    const weights = activeRarities.map(r => r.base_percent);

    const selectedRarityName = weightedRandom(population, weights);
    const selectedRarity = activeRarities.find(r => r.name === selectedRarityName) as Rarity;
    const rarityStr = `${selectedRarity.emoji} ${selectedRarity.name}`;

    const allCharacters = await mongodb.getAllCharacters();
    if (!allCharacters || allCharacters.length === 0) return;

    let pool = allCharacters.filter(c => c.rarity === rarityStr);
    if (pool.length === 0) {
        pool = allCharacters.filter(c => c.rarity === "⚪ Common");
    }

    if (pool.length === 0) return;

    if (!sentCharacters[chatId]) {
        sentCharacters[chatId] = [];
    }

    let unSent = pool.filter(c => !sentCharacters[chatId].includes(c.id));
    if (unSent.length === 0) {
        sentCharacters[chatId] = [];
        unSent = pool;
    }

    const character = unSent[Math.floor(Math.random() * unSent.length)];
    sentCharacters[chatId].push(character.id);
    lastCharacters[chatId] = character;

    if (firstCorrectGuesses[chatId]) {
        delete firstCorrectGuesses[chatId];
    }

    const markup = Markup.inlineKeyboard([
        [Markup.button.url("Catch Guide 📖", "https://t.me/SenpaiXWaifu_Bot?start=help")]
    ]);

    try {
        await bot.telegram.sendPhoto(
            chatId,
            character.img_url,
            {
                caption: formatString(ctx.lang.spawn_msg || "A Wild **{0}** Character Appeared! 🌟\n\nUse `/guess <Character Name>` to catch them and add them to your collection!", character.rarity),
                parse_mode: 'Markdown',
                reply_markup: markup.reply_markup
            }
        );
    } catch (e: any) {
        if (e.code === 429) { // Flood wait
            const retryAfter = e.parameters?.retry_after || 1;
            setTimeout(async () => {
                try {
                    await bot.telegram.sendPhoto(
                        chatId,
                        character.img_url,
                        {
                            caption: formatString(ctx.lang.spawn_msg || "A Wild **{0}** Character Appeared! 🌟\n\nUse `/guess <Character Name>` to catch them and add them to your collection!", character.rarity),
                            parse_mode: 'Markdown',
                            reply_markup: markup.reply_markup
                        }
                    );
                } catch (err) {}
            }, (retryAfter + 1) * 1000);
        }
    }
}

export function register(bot: Telegraf<SenpaiContext>) {
    const guessCommands = ["/guess", "/protecc", "/collect", "/grab", "/hunt"];

    bot.on('message', languageMiddleware(), async (ctx, next) => {
        // Skip if private or from bot
        if (ctx.chat.type === 'private' || ctx.from?.is_bot) {
            return next();
        }

        // Check if it's one of the guess commands, skip counter logic
        if (ctx.message && 'text' in ctx.message) {
            const text = ctx.message.text.split('@')[0]; // Handle /guess@botname
            if (guessCommands.some(c => text.startsWith(c))) {
                return next();
            }
        }

        const chatId = ctx.chat.id;

        if (messageCounts[chatId]) {
            messageCounts[chatId] += 1;
        } else {
            messageCounts[chatId] = 1;
        }

        // The python version says message_frequency = 100 but later changetime can update it.
        // changetime plugin uses a separate collection? No, Python version has `message_frequency = 100` hardcoded in spawner.py but there's a changetime.py
        // We'll hardcode 100 here. 
        // Wait, changetime updates DB or something? Let me just use 100 and then I'll check changetime.py later
        // Actually, Python version says `message_frequency = 100` fixed inside `message_counter`. Let's strictly follow it.
        const messageFrequency = 100;

        if (messageCounts[chatId] % messageFrequency === 0) {
            await sendImage(bot, ctx, chatId);
            messageCounts[chatId] = 0;
        }

        return next();
    });

    bot.command(['guess', 'protecc', 'collect', 'grab', 'hunt'], languageMiddleware(), async (ctx) => {
        const chatId = ctx.chat.id;
        const userId = ctx.from?.id;
        if (!userId) return;

        if (!lastCharacters[chatId]) return;

        if (firstCorrectGuesses[chatId]) {
            return await ctx.reply(ctx.lang.spawner_already);
        }

        const text = ctx.message.text;
        const commandParts = text.split(' ');
        const guessText = commandParts.slice(1).join(' ').toLowerCase();

        if (!guessText) return;

        const charName = lastCharacters[chatId].name.toLowerCase();
        const nameParts = charName.split(' ');

        const sortedNameParts = [...nameParts].sort().join(' ');
        const sortedGuessParts = guessText.split(' ').sort().join(' ');

        if (sortedNameParts === sortedGuessParts || nameParts.includes(guessText)) {
            firstCorrectGuesses[chatId] = userId;

            await mongodb.updateUser(userId, {
                username: ctx.from.username,
                first_name: ctx.from.first_name
            });
            await mongodb.addCharacterToUser(userId, lastCharacters[chatId]);

            await ctx.reply(
                formatString(
                    ctx.lang.guess_success || "🎉 **YATTA! {0}**\n\nYou successfully caught a new character!\n\n🏷 **Name:** {1}\n📺 **Anime:** {2}\n✨ **Rarity:** {3}\n\n*This character has been added to your harem.*",
                    ctx.from.first_name,
                    lastCharacters[chatId].name,
                    lastCharacters[chatId].anime,
                    lastCharacters[chatId].rarity
                ),
                { parse_mode: 'Markdown' }
            );
        } else {
            await ctx.reply(ctx.lang.spawner_fail);
        }
    });
}
