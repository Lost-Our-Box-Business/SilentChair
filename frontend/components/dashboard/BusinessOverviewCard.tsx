"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Send, CheckCircle2, Building2 } from "lucide-react";
import { getBusinessContext, correctBusinessContext, type BusinessContext } from "@/lib/living-doc-api";
import { useTranslations, useLocale } from "next-intl";

interface Props {
  businessId: string;
}

export function BusinessOverviewCard({ businessId }: Props) {
  const t = useTranslations("businessOps");
  const locale = useLocale();
  const [context, setContext] = useState<BusinessContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [correction, setCorrection] = useState("");
  const [correcting, setCorrecting] = useState(false);
  const [corrected, setCorrected] = useState(false);
  const successTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getBusinessContext(businessId, locale)
      .then(setContext)
      .catch(() => {})
      .finally(() => setLoading(false));
    return () => {
      if (successTimer.current) clearTimeout(successTimer.current);
    };
  }, [businessId]);

  async function handleCorrect() {
    if (!correction.trim() || correcting) return;
    setCorrecting(true);
    try {
      const updated = await correctBusinessContext(businessId, correction.trim());
      setContext(updated);
      setCorrection("");
      setCorrected(true);
      successTimer.current = setTimeout(() => setCorrected(false), 3000);
    } catch {
      // silent — user can try again
    } finally {
      setCorrecting(false);
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="h-4 w-32 rounded bg-muted animate-pulse" />
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="h-3 w-full rounded bg-muted animate-pulse" />
          <div className="h-3 w-5/6 rounded bg-muted animate-pulse" />
          <div className="h-3 w-4/6 rounded bg-muted animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (!context?.summary) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground" />
          {t("businessOverview")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground leading-relaxed">{context.summary}</p>

        <div className="flex items-center gap-2">
          <Input
            className="h-8 text-xs"
            placeholder={t("overviewPlaceholder")}
            value={correction}
            onChange={(e) => setCorrection(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleCorrect(); }}
            disabled={correcting}
          />
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 shrink-0"
            onClick={handleCorrect}
            disabled={!correction.trim() || correcting}
          >
            {correcting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : corrected ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
