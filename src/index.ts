import { config } from './config';
config.check();

import { logger } from './core/logger';
import { senpai, bot } from './core/bot';
import { mongodb } from './core/mongo';
import { registerPlugins } from './plugins';

async function main() {
    try {
        await mongodb.connect();
        await mongodb.initializeRarities();

        registerPlugins(bot);

        // Required TS-specific crash-resilience (Global error handler)
        bot.catch((err: any, ctx) => {
            logger.error(`Unhandled error for ${ctx.updateType}`, err);
        });

        await senpai.start();
        await bot.launch();
        
        logger.info("Bot started successfully!");

        // Enable graceful stop
        process.once('SIGINT', () => senpai.stop('SIGINT'));
        process.once('SIGTERM', () => senpai.stop('SIGTERM'));
    } catch (err: any) {
        logger.error("Failed to start bot", err);
        process.exit(1);
    }
}

main();
