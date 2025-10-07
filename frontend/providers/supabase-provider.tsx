// frontend\providers\supabase-provider.tsx
"use client";

import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase-client";
import { SupabaseContextType, SupabaseProviderProps } from "@/lib/types";

const SupabaseContext = createContext<SupabaseContextType | undefined>(undefined);

export const useSupabase = (): SupabaseContextType => {
  const context = useContext(SupabaseContext);
  if (!context) throw new Error("useSupabase must be used within SupabaseProvider");
  return context;
};

export const SupabaseProvider: React.FC<SupabaseProviderProps> = ({ children }) => {
  const [session, setSession] = useState<Session|null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
        if (sessionError) throw sessionError;
        if (isMounted) setSession(currentSession);

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
          if (isMounted) setSession(newSession);
        });

        return () => subscription.unsubscribe();
      } catch (err: any) {
        if (isMounted) setError(err.message ?? "Authentication failed");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    const cleanup = initializeAuth();
    return () => {
      isMounted = false;
      cleanup.then(fn => fn?.()).catch(() => {});
    };
  }, []);

const value = useMemo(
  () => ({ supabase, session, isLoading, error }),
  [session, isLoading, error]
);

return (
  <SupabaseContext.Provider value={value}>
    {children}
  </SupabaseContext.Provider>
);

};







// | Use case                                                         | Recommended approach                                                                                                   |
// | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
// | Access Supabase DB (queries, RPCs, realtime)                     | Use the **singleton client** directly. This can be done anywhere: stores, utils, React components. No provider needed. |
// | Access session / auth state reactively in React components/pages | Use **SupabaseProvider + `useSupabase`**. This keeps session in state and triggers re-renders when it changes.         |