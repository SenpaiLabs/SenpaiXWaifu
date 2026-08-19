import { Telegraf } from 'telegraf';
import { SenpaiContext } from '../core/bot';
import { logger } from '../core/logger';

import * as broadcast from './broadcast';
import * as changetime from './changetime';
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
import * as trade from './trade';
import * as upload from './upload';

export function registerPlugins(bot: Telegraf<SenpaiContext>) {
    const plugins = [
        broadcast,
        changetime,
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
        trade,
        upload
    ];

    for (const plugin of plugins) {
        plugin.register(bot);
    }

    logger.info(`Loaded ${plugins.length} modules.`);
}
