import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';
import { mongodb } from '../core/mongo';

export function register(bot: Telegraf<SenpaiContext>) {
    bot.on('inline_query', languageMiddleware(), async (ctx) => {
        const query = ctx.inlineQuery.query.trim();
        const isCollection = query.toLowerCase().startsWith('collection');
        const searchTerm = isCollection ? query.slice(10).trim().toLowerCase() : query.toLowerCase();

        let characters: any[] = [];

        if (isCollection) {
            // Search user's harem
            const user = await mongodb.getUser(ctx.from.id);
            if (user && user.characters) {
                characters = user.characters;
                if (searchTerm) {
                    characters = characters.filter(c => 
                        c.name.toLowerCase().includes(searchTerm) || 
                        c.anime.toLowerCase().includes(searchTerm)
                    );
                }
            }
        } else {
            // Search global database
            const allCharacters = await mongodb.getAllCharacters();
            characters = allCharacters;
            if (searchTerm) {
                characters = characters.filter(c => 
                    c.name.toLowerCase().includes(searchTerm) || 
                    c.anime.toLowerCase().includes(searchTerm)
                );
            }
        }

        // Limit results to 50 for inline queries
        const limitedResults = characters.slice(0, 50);

        const results = limitedResults.map((chara, index) => {
            const caption = `**Name:** ${chara.name}\n**Anime:** ${chara.anime}\n**Rarity:** ${chara.rarity}` + 
                            (isCollection ? `\n**Owner:** [${ctx.from.first_name}](tg://user?id=${ctx.from.id})` : "");

            return {
                type: 'photo',
                id: `${chara.id}_${index}`,
                photo_url: chara.img_url,
                thumb_url: chara.img_url,
                caption: caption,
                parse_mode: 'Markdown'
            };
        });

        if (results.length === 0) {
            return await ctx.answerInlineQuery([
                {
                    type: 'article',
                    id: 'no_results',
                    title: 'No characters found',
                    description: 'Try searching something else!',
                    input_message_content: {
                        message_text: '❌ No characters found matching that search!'
                    }
                }
            ], { cache_time: 1, is_personal: isCollection });
        }

        await ctx.answerInlineQuery(results as any, { cache_time: 1, is_personal: isCollection });
    });
}
