export class TTLCache<K, V> {
    private cache = new Map<K, { value: V; expiresAt: number }>();
    private ttlMs: number;

    constructor(ttlMs: number) {
        this.ttlMs = ttlMs;
    }

    set(key: K, value: V) {
        this.cache.set(key, {
            value,
            expiresAt: Date.now() + this.ttlMs
        });
    }

    get(key: K): V | undefined {
        const item = this.cache.get(key);
        if (!item) return undefined;
        
        if (Date.now() > item.expiresAt) {
            this.cache.delete(key);
            return undefined;
        }

        return item.value;
    }

    delete(key: K) {
        this.cache.delete(key);
    }
    
    clear() {
        this.cache.clear();
    }
}
