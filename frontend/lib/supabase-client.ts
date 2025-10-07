
// frontend/lib/supabase-client.ts// frontend/lib/supabase-client.ts
import { createClient } from "@supabase/supabase-js";
import { CLIENT_CONFIG } from "./client_config";

// Single Supabase client instance for frontend
export const supabase = createClient(
  CLIENT_CONFIG.supabaseUrl,
  CLIENT_CONFIG.supabaseAnonKey
);
