import { MongoClient, Db, Collection } from 'mongodb';
import { config } from '../config';
import { TTLCache } from '../utils/ttlCache';

export interface Rarity {
    id: string;
    name: string;
    emoji: string;
    base_percent: number;
    active: boolean;
}

export interface Character {
    id: string;
    [key: string]: any;
}

export interface User {
    id: number;
    characters?: Character[];
    [key: string]: any;
}

export interface Chat {
    id: number;
    title: string;
}

export interface SudoersDb {
    sudo: string;
    sudoers?: number[];
    uploaders?: number[];
}

class MongoDB {
    mongo: MongoClient;
    db: Db;
    characters: Collection<Character>;
    users: Collection<User>;
    chats: Collection<Chat>;
    sudoersdb: Collection<SudoersDb>;
    rarity_settings: Collection<Rarity>;
    cache: TTLCache<string, any>;

    constructor() {
        this.mongo = new MongoClient(config.MONGO_URL);
        this.db = this.mongo.db('Senpai');
        this.characters = this.db.collection<Character>('characters');
        this.users = this.db.collection<User>('users');
        this.chats = this.db.collection<Chat>('chats');
        this.sudoersdb = this.db.collection<SudoersDb>('sudoersdb');
        this.rarity_settings = this.db.collection<Rarity>('rarity_settings');
        this.cache = new TTLCache<string, any>(600 * 1000); // 10 min cache
    }

    async connect() {
        await this.mongo.connect();
    }

    async initializeRarities() {
        const default_rarities: Rarity[] = [
            { id: "1", name: "Common", emoji: "⚪", base_percent: 45, active: true },
            { id: "2", name: "Rare", emoji: "🔵", base_percent: 30, active: true },
            { id: "3", name: "Legendary", emoji: "🟡", base_percent: 20, active: true },
            { id: "4", name: "Special", emoji: "💮", base_percent: 12, active: true },
            { id: "5", name: "Limited", emoji: "🔮", base_percent: 8, active: true },
            { id: "6", name: "Kawaii", emoji: "🍭", base_percent: 6, active: true },
            { id: "7", name: "Celestial", emoji: "🎐", base_percent: 4, active: true },
            { id: "8", name: "Cross Version", emoji: "🧬", base_percent: 2, active: true },
            { id: "9", name: "Winter", emoji: "❄️", base_percent: 10, active: false },
            { id: "10", name: "Summer", emoji: "⛅", base_percent: 10, active: false },
            { id: "11", name: "Rain", emoji: "☔", base_percent: 10, active: false },
            { id: "12", name: "Halloween", emoji: "🎃", base_percent: 10, active: false },
            { id: "13", name: "Christmas", emoji: "🎄", base_percent: 10, active: false },
            { id: "14", name: "Valentine", emoji: "💝", base_percent: 10, active: false },
            { id: "15", name: "Auction", emoji: "🪩", base_percent: 0, active: false },
            { id: "16", name: "Premium Edition", emoji: "💸", base_percent: 0, active: false }
        ];

        const count = await this.rarity_settings.countDocuments({});
        if (count === 0) {
            await this.rarity_settings.insertMany(default_rarities);
        }
    }

    async getActiveRarities(): Promise<Rarity[]> {
        const cached = this.cache.get("active_rarities");
        if (cached) {
            return cached;
        }

        const active = await this.rarity_settings.find({ active: true }).toArray();
        this.cache.set("active_rarities", active);
        return active;
    }

    async getAllRarities(): Promise<Rarity[]> {
        return await this.rarity_settings.find({}).toArray();
    }

    async setRarityStatus(rarity_id: string, status: boolean): Promise<boolean> {
        const result = await this.rarity_settings.updateOne({ id: rarity_id }, { $set: { active: status } });
        if (result.modifiedCount > 0 || result.matchedCount > 0) {
            this.cache.delete("active_rarities");
            return true;
        }
        return false;
    }

    async getAllCharacters(): Promise<Character[]> {
        return await this.characters.find({}).toArray();
    }

    async searchCharacters(query: string, limit: number = 50): Promise<Character[]> {
        if (!query) {
            return await this.characters.find({}).limit(limit).toArray();
        }
        return await this.characters.find({
            $or: [
                { name: { $regex: query, $options: "i" } },
                { anime: { $regex: query, $options: "i" } }
            ]
        }).limit(limit).toArray();
    }

    async getUser(user_id: number): Promise<User | null> {
        return await this.users.findOne({ id: user_id });
    }

    async updateUser(user_id: number, update_data: any) {
        await this.users.updateOne({ id: user_id }, { $set: update_data }, { upsert: true });
    }

    async addCharacterToUser(user_id: number, character: Character) {
        await this.users.updateOne({ id: user_id }, { $push: { characters: character } } as any, { upsert: true });
    }

    // Chat management
    async addChat(chat_id: number, title: string) {
        await this.chats.updateOne({ id: chat_id }, { $set: { title } }, { upsert: true });
    }

    async getAllChats(): Promise<Chat[]> {
        return await this.chats.find({}).toArray();
    }

    async removeChat(chat_id: number) {
        await this.chats.deleteOne({ id: chat_id });
    }

    // Sudo management
    async getSudoers(): Promise<number[]> {
        const cached = this.cache.get("sudoers");
        if (cached) {
            return cached;
        }

        const sudoers = await this.sudoersdb.findOne({ sudo: "sudo" });
        if (!sudoers) {
            this.cache.set("sudoers", []);
            return [];
        }

        const sudo_list = sudoers.sudoers || [];
        this.cache.set("sudoers", sudo_list);
        return sudo_list;
    }

    async addSudo(user_id: number): Promise<boolean> {
        const sudoers = await this.getSudoers();
        if (!sudoers.includes(user_id)) {
            sudoers.push(user_id);
            await this.sudoersdb.updateOne(
                { sudo: "sudo" }, { $set: { sudoers: sudoers } }, { upsert: true }
            );
            this.cache.set("sudoers", sudoers);
        }
        return true;
    }

    async delSudo(user_id: number): Promise<boolean> {
        let sudoers = await this.getSudoers();
        if (sudoers.includes(user_id)) {
            sudoers = sudoers.filter(id => id !== user_id);
            await this.sudoersdb.updateOne(
                { sudo: "sudo" }, { $set: { sudoers: sudoers } }, { upsert: true }
            );
            this.cache.set("sudoers", sudoers);
        }
        return true;
    }

    // Uploader management
    async getUploaders(): Promise<number[]> {
        const cached = this.cache.get("uploaders");
        if (cached) {
            return cached;
        }

        const uploaders = await this.sudoersdb.findOne({ sudo: "uploaders" });
        if (!uploaders) {
            this.cache.set("uploaders", []);
            return [];
        }

        const uploader_list = uploaders.uploaders || [];
        this.cache.set("uploaders", uploader_list);
        return uploader_list;
    }

    async addUploader(user_id: number): Promise<boolean> {
        const uploaders = await this.getUploaders();
        if (!uploaders.includes(user_id)) {
            uploaders.push(user_id);
            await this.sudoersdb.updateOne(
                { sudo: "uploaders" }, { $set: { uploaders: uploaders } }, { upsert: true }
            );
            this.cache.set("uploaders", uploaders);
        }
        return true;
    }

    async delUploader(user_id: number): Promise<boolean> {
        let uploaders = await this.getUploaders();
        if (uploaders.includes(user_id)) {
            uploaders = uploaders.filter(id => id !== user_id);
            await this.sudoersdb.updateOne(
                { sudo: "uploaders" }, { $set: { uploaders: uploaders } }, { upsert: true }
            );
            this.cache.set("uploaders", uploaders);
        }
        return true;
    }

    async deleteCharacter(char_id: string) {
        return await this.characters.deleteOne({ id: char_id });
    }
}

export const mongodb = new MongoDB();
