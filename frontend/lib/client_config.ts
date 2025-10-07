// frontend\lib\client_config.ts
// client-safe config
export const CLIENT_CONFIG = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  backend_api_url: process.env.NEXT_PUBLIC_BACKEND_API_URL!,
  ai_api_key: process.env.NEXT_PUBLIC_AI_API_KEY!,
};
