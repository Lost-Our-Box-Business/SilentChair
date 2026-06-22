"use client";

import { useState, useTransition } from "react";
import { useTranslations } from "next-intl";
import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { setLocale } from "@/app/actions/locale";
import { locales, localeNames } from "@/i18n/config";

export default function ProfileSettingsPage() {
  const t = useTranslations("profile");
  const tLang = useTranslations("language");
  const locale = useLocale();
  const router = useRouter();
  const [selectedLocale, setSelectedLocale] = useState(locale);
  const [isPending, startTransition] = useTransition();
  const [saved, setSaved] = useState(false);

  function handleSave() {
    startTransition(async () => {
      await setLocale(selectedLocale);
      setSaved(true);
      router.refresh();
      setTimeout(() => setSaved(false), 3000);
    });
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">{t("language")}</CardTitle>
          <CardDescription className="text-xs">{t("languageDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs">{tLang("label")}</Label>
            <select
              value={selectedLocale}
              onChange={(e) => { setSelectedLocale(e.target.value); setSaved(false); }}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              {locales.map((l) => (
                <option key={l} value={l}>{localeNames[l]}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isPending || selectedLocale === locale}
            >
              {isPending ? t("saving") : t("saveChanges")}
            </Button>
            {saved && (
              <span className="text-xs text-green-600 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> {t("saved")}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="opacity-60">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">{t("displayName")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">{t("timezonePlaceholder")}</p>
        </CardContent>
      </Card>

      <Card className="opacity-60">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">{t("timezone")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">{t("timezonePlaceholder")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
