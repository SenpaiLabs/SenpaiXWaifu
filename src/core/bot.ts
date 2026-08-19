import { Telegraf, Context } from 'telegraf';
import { config } from '../config';
import { mongodb } from './mongo';
import { logger } from './logger';

// Extend the Telegraf Context to include custom properties
export interface SenpaiContext extends Context {
    lang: Record<string, string>;
}

export class SenpaiBot {
    bot: Telegraf<SenpaiContext>;
    owner: number;
    sudoers: Set<number>;
    uploaders: Set<number>;

    constructor() {
        this.bot = new Telegraf<SenpaiContext>(config.BOT_TOKEN);
        this.owner = config.OWNER_ID;
        this.sudoers = new Set();
        this.uploaders = new Set();
    }

    async start() {
        // Load Sudoers from DB
        const sudolist = await mongodb.getSudoers();
        for (const userId of sudolist) {
            this.sudoers.add(userId);
        }
        if (!this.sudoers.has(this.owner)) {
            this.sudoers.add(this.owner);
        }

        // Load Uploaders from DB
        const uploaderlist = await mongodb.getUploaders();
        for (const userId of uploaderlist) {
            this.uploaders.add(userId);
        }

        logger.info(`Bot Started! Loaded ${this.sudoers.size} sudo users and ${this.uploaders.size} uploaders.`);
    }

    async stop(reason?: string) {
        this.bot.stop(reason);
        logger.info("Bot Stopped!");
    }
}

export const senpai = new SenpaiBot();
export const bot = senpai.bot;
