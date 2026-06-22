"use server";

import { cookies } from "next/headers";
import { createClient } from "@/lib/supabase/server";
import { locales, defaultLocale } from "@/i18n/config";

export async function setLocale(locale: string) {
  const resolved = locales.includes(locale as (typeof locales)[number]) ? locale : defaultLocale;
  const cookieStore = await cookies();
  cookieStore.set("locale", resolved, { path: "/", maxAge: 60 * 60 * 24 * 365 });

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (user) {
    await supabase.auth.updateUser({ data: { language: resolved } });
  }
}
