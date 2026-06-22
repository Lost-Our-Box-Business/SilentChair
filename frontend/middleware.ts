import { NextRequest, NextResponse } from "next/server";
import { locales, defaultLocale } from "./i18n/config";

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  if (!request.cookies.get("locale")) {
    const accepted = request.headers.get("accept-language") ?? "";
    const preferred = accepted.split(",")[0].split("-")[0].toLowerCase();
    const locale = locales.includes(preferred as (typeof locales)[number]) ? preferred : defaultLocale;
    response.cookies.set("locale", locale, { path: "/", maxAge: 60 * 60 * 24 * 365 });
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next|api|favicon|.*\\..*).*)"],
};
