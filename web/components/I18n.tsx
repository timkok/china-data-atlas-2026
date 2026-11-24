"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { ui, type Lang } from "@/lib/i18n";

const I18nContext = createContext<{ lang: Lang; t: { [K in keyof (typeof ui)["zh"]]: string }; toggle: () => void }>({
  lang: "zh",
  t: ui.zh,
  toggle: () => undefined,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>("zh");
  useEffect(() => {
    const saved = window.localStorage.getItem("cda-lang");
    if (saved === "en" || saved === "zh") setLang(saved);
  }, []);
  const toggle = () => {
    const next: Lang = lang === "zh" ? "en" : "zh";
    setLang(next);
    window.localStorage.setItem("cda-lang", next);
    document.documentElement.lang = next === "zh" ? "zh-CN" : "en";
  };
  return <I18nContext.Provider value={{ lang, t: ui[lang], toggle }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
