import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { logger } from '../core/logger';

import * as broadcast from './broadcast';
import * as harem from './harem';
import * as iquery from './iquery';
import * as leaderboard from './leaderboard';
import * as pluginLogger from './logger';
import * as ping from './ping';
import * as rmanager from './rmanager';
import * as spawner from './spawner';
import * as start from './start';
import * as sudos from './sudos';
import * as tgm from './tgm';
import * as upload from './upload';

export function registerPlugins(bot: Telegraf<SenpaiContext>) {
    const plugins = [
        broadcast,
        harem,
        iquery,
        leaderboard,
        pluginLogger,
        ping,
        rmanager,
        spawner,
        start,
        sudos,
        tgm,
        upload
    ];

    for (const plugin of plugins) {
        plugin.register(bot);
    }

    logger.info(`Loaded ${plugins.length} modules.`);
}
