import fs from 'fs';
import path from 'path';
import { SenpaiContext } from '../core/bot';
import enLocale from '../locales/en.json';

export const LOCALES: Record<string, Record<string, string>> = {
    'en': enLocale
};

export function languageMiddleware() {
    return async (ctx: SenpaiContext, next: () => Promise<void>) => {
        // Hardcode English for now just like Python version
        const langCode = 'en';
        ctx.lang = LOCALES[langCode] || LOCALES['en'] || {};
        return next();
    };
}
