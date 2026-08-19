import fs from 'fs';
import path from 'path';
import { SenpaiContext } from '../core/bot';

export const LOCALES: Record<string, Record<string, string>> = {};

function loadLocales() {
    const localesDir = path.join(__dirname, '..', 'locales');
    if (fs.existsSync(localesDir)) {
        const files = fs.readdirSync(localesDir);
        for (const file of files) {
            if (file.endsWith('.json')) {
                const langCode = file.split('.')[0];
                const content = fs.readFileSync(path.join(localesDir, file), 'utf-8');
                LOCALES[langCode] = JSON.parse(content);
            }
        }
    }
}

loadLocales();

export function languageMiddleware() {
    return async (ctx: SenpaiContext, next: () => Promise<void>) => {
        // Hardcode English for now just like Python version
        const langCode = 'en';
        ctx.lang = LOCALES[langCode] || LOCALES['en'] || {};
        return next();
    };
}
