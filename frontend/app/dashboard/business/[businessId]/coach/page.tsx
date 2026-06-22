import { getTranslations } from "next-intl/server";

export default async function CoachPage() {
  const t = await getTranslations("coach");
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-2">{t("title")}</h1>
      <p className="text-muted-foreground">{t("comingSoon")}</p>
    </div>
  );
}
