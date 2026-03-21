import { useState, useCallback, createContext, useContext } from 'react';
import { zh } from './zh';
import { en } from './en';

const langs = { zh, en } as const;
export type Lang = keyof typeof langs;
export type { Translations } from './zh';

export function useLanguage() {
  const [lang, setLang] = useState<Lang>(
    () => (localStorage.getItem('lang') as Lang) || 'zh',
  );

  const t = langs[lang];

  const switchLang = useCallback((l: Lang) => {
    setLang(l);
    localStorage.setItem('lang', l);
  }, []);

  return { t, lang, switchLang };
}

// Context-based approach for sharing language state across the app
export const LanguageContext = createContext<ReturnType<typeof useLanguage> | null>(null);

export function useT() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    // Fallback: return zh translations directly when used outside provider
    return langs['zh'];
  }
  return ctx.t;
}
