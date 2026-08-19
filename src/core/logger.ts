import fs from 'fs';
import path from 'path';

const logFile = path.join(process.cwd(), 'log.txt');

function formatMessage(level: string, message: string): string {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    return `${timestamp} - ${level} - bot - ${message}\n`;
}

function writeLog(level: string, message: string) {
    const formatted = formatMessage(level, message);
    if (level === 'ERROR') {
        console.error(formatted.trim());
    } else {
        console.log(formatted.trim());
    }
    fs.appendFileSync(logFile, formatted);
}

export const logger = {
    info: (msg: string) => writeLog('INFO', msg),
    error: (msg: string, err?: any) => {
        writeLog('ERROR', err ? `${msg} ${err.stack || err}` : msg);
    },
    warn: (msg: string) => writeLog('WARNING', msg),
    debug: (msg: string) => writeLog('DEBUG', msg)
};
