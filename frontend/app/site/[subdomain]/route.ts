import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

function getServiceSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_SERVICE_ROLE_KEY is not set in environment variables");
  }
  return createClient(url, key);
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ subdomain: string }> },
) {
  const { subdomain } = await params;
  const supabase = getServiceSupabase();

  const { data } = await supabase
    .from("websites")
    .select("files, status")
    .eq("subdomain", subdomain)
    .single();

  if (!data || data.status !== "published") {
    return new NextResponse("Not found", { status: 404 });
  }

  const files: Array<{ path: string; content: string }> = data.files ?? [];
  const indexFile = files.find((f) => f.path === "index.html");

  if (!indexFile) {
    return new NextResponse("No index.html found", { status: 404 });
  }

  return new NextResponse(indexFile.content, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

export const dynamic = "force-dynamic";
