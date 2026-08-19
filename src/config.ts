import { config as loadDotenv } from 'dotenv';

loadDotenv();

class Config {
    BOT_TOKEN: string;
    MONGO_URL: string;
    OWNER_ID: number;
    START_IMG: string;

    constructor() {
        this.BOT_TOKEN = process.env.BOT_TOKEN || "";
        this.MONGO_URL = process.env.MONGO_URL || "";
        this.OWNER_ID = parseInt(process.env.OWNER_ID || "0", 10);
        this.START_IMG = process.env.START_IMG || "";
    }

    check() {
        const requiredKeys: (keyof Config)[] = ["BOT_TOKEN", "MONGO_URL", "OWNER_ID"];
        const missing = requiredKeys.filter(key => {
            const val = this[key];
            return val === undefined || val === null || val === "" || (typeof val === "number" && isNaN(val));
        });
        
        if (missing.length > 0) {
            console.error(`Missing required environment variables: ${missing.join(', ')}`);
            process.exit(1);
        }
    }
}

export const config = new Config();
