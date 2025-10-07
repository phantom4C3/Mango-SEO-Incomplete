// frontend\lib\server_config.ts
// server-only config (import only in server code)
export const SERVER_CONFIG = {
 supabaseServiceKey: process.env.SUPABASE_SERVICE_KEY!,
  upstashRedisRestUrl: process.env.UPSTASH_REDIS_REST_URL!,
  upstashRedisRestToken: process.env.UPSTASH_REDIS_REST_TOKEN!,

};