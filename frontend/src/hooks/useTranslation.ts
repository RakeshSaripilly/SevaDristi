import { useState, useEffect } from 'react';
import type { SupportedLocale } from '../types';

import enIN from '../locales/en-IN.json';
import teIN from '../locales/te-IN.json';
import hiIN from '../locales/hi-IN.json';
import taIN from '../locales/ta-IN.json';
import knIN from '../locales/kn-IN.json';
import mlIN from '../locales/ml-IN.json';
import mrIN from '../locales/mr-IN.json';
import bnIN from '../locales/bn-IN.json';
import guIN from '../locales/gu-IN.json';
import orIN from '../locales/or-IN.json';
import paIN from '../locales/pa-IN.json';
import asIN from '../locales/as-IN.json';

const translations: Record<SupportedLocale, Record<string, string>> = {
  'en-IN': enIN,
  'te-IN': teIN,
  'hi-IN': hiIN,
  'ta-IN': taIN,
  'kn-IN': knIN,
  'ml-IN': mlIN,
  'mr-IN': mrIN,
  'bn-IN': bnIN,
  'gu-IN': guIN,
  'or-IN': orIN,
  'pa-IN': paIN,
  'as-IN': asIN,
};

export const SUPPORTED_LANGUAGES: { code: SupportedLocale; name: string; nativeName: string }[] = [
  { code: 'te-IN', name: 'Telugu', nativeName: 'తెలుగు' },
  { code: 'en-IN', name: 'English', nativeName: 'English' },
  { code: 'hi-IN', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'ta-IN', name: 'Tamil', nativeName: 'தமிழ்' },
  { code: 'kn-IN', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
  { code: 'ml-IN', name: 'Malayalam', nativeName: 'മലയാളം' },
  { code: 'mr-IN', name: 'Marathi', nativeName: 'मराठी' },
  { code: 'bn-IN', name: 'Bengali', nativeName: 'বাংলা' },
  { code: 'gu-IN', name: 'Gujarati', nativeName: 'ગુજરાતી' },
  { code: 'or-IN', name: 'Odia', nativeName: 'ଓଡ଼ିଆ' },
  { code: 'pa-IN', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
  { code: 'as-IN', name: 'Assamese', nativeName: 'অসমীয়া' },
];

export function useTranslation() {
  const [locale, setLocale] = useState<SupportedLocale>(() => {
    return (localStorage.getItem('sevadristi_locale') as SupportedLocale) || 'te-IN';
  });

  useEffect(() => {
    localStorage.setItem('sevadristi_locale', locale);
    document.documentElement.lang = locale.split('-')[0];
  }, [locale]);

  const t = (key: string, fallback?: string): string => {
    const currentDict = translations[locale] || translations['en-IN'];
    if (currentDict && currentDict[key]) {
      return currentDict[key];
    }
    const defaultDict = translations['en-IN'];
    if (defaultDict && defaultDict[key]) {
      return defaultDict[key];
    }
    return fallback || key;
  };

  return { locale, setLocale, t, languages: SUPPORTED_LANGUAGES };
}
