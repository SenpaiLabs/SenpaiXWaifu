import { Markup } from 'telegraf';

export function startMarkup(lang: Record<string, string>, isPrivate: boolean = true) {
    if (isPrivate) {
        return Markup.inlineKeyboard([
            [Markup.button.url(lang.btn_1 || "Add Me", "https://t.me/SenpaiXWaifu_Bot?startgroup=true")],
            [
                Markup.button.callback(lang.btn_2 || "Help", "help_menu"),
                Markup.button.url(lang.btn_3 || "Support", "https://t.me/Collect_em_support")
            ],
            [Markup.button.url(lang.btn_4 || "Source", "https://github.com/SenpaiLabs/SenpaiXWaifu")]
        ]);
    } else {
        return Markup.inlineKeyboard([
            [Markup.button.url(lang.btn_5 || "Start Private", "https://t.me/SenpaiXWaifu_Bot?start=true")]
        ]);
    }
}

export function helpMarkup(lang: Record<string, string>) {
    return Markup.inlineKeyboard([
        [Markup.button.callback(lang.btn_6 || "Back", "start_menu")]
    ]);
}
