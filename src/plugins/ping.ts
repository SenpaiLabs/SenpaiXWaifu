import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { languageMiddleware } from '../utils/locales';

const START_TIME = Date.now();

function getReadableTime(seconds: number): string {
    let count = 0;
    let pingTime = "";
    const timeList: string[] = [];
    const timeSuffixList = ["s", "m", "h", "days"];
    
    while (count < 4) {
        count += 1;
        const remainder = count < 4 ? (count < 3 ? seconds % 60 : seconds % 24) : seconds;
        const result = count < 4 ? (count < 3 ? Math.floor(seconds / 60) : Math.floor(seconds / 24)) : 0;
        
        if (seconds === 0 && remainder === 0) {
            break;
        }
        timeList.push(Math.floor(remainder).toString());
        seconds = result;
    }

    for (let x = 0; x < timeList.length; x++) {
        timeList[x] = timeList[x] + timeSuffixList[x];
    }

    if (timeList.length === 4) {
        pingTime += timeList.pop() + ", ";
    }
    timeList.reverse();
    pingTime += timeList.join(":");
    return pingTime || "0s";
}

// Equivalent to Python's .format() for the specific cases used in the locale files
export function formatString(str: string, ...args: any[]) {
    return str.replace(/{(\d+)(?::\.\d+f)?}/g, (match, number) => {
        const val = args[number];
        if (match.includes(':.')) {
            const precisionStr = match.split('.')[1];
            const precision = parseInt(precisionStr.substring(0, precisionStr.length - 1));
            return Number(val).toFixed(precision);
        }
        return typeof val !== 'undefined' ? val : match;
    });
}

export function register(bot: Telegraf<SenpaiContext>) {
    bot.command('ping', languageMiddleware(), async (ctx) => {
        const start = Date.now();
        const msg = await ctx.reply(ctx.lang.ping_1);
        const end = Date.now();
        
        const resp = (end - start);
        const uptimeSeconds = Math.floor((Date.now() - START_TIME) / 1000);
        const uptime = getReadableTime(uptimeSeconds);
        
        const formattedText = formatString(
            ctx.lang.ping_2,
            resp,
            uptime
        );
        
        await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, formattedText, { parse_mode: 'Markdown' });
    });
}
