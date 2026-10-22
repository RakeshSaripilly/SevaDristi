import React from 'react';
import { ShieldCheck, Wifi, WifiOff, Globe, Monitor, UserCheck } from 'lucide-react';
import { useTranslation, SUPPORTED_LANGUAGES } from '../hooks/useTranslation';
import type { SupportedLocale } from '../types';

interface HeaderProps {
  currentView: 'citizen' | 'operator';
  onViewChange: (view: 'citizen' | 'operator') => void;
  isOnline: boolean;
  processingMode?: 'real' | 'demo';
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onViewChange,
  isOnline,
  processingMode = 'demo'
}) => {
  const { locale, setLocale, t } = useTranslation();

  return (
    <header className="sticky top-0 z-50 glass-panel shadow-sm border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-tsblue-700 flex items-center justify-center text-white shadow-md">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">{t('app_title')}</h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                v2026.1
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">{t('app_subtitle')}</p>
          </div>
        </div>

        {/* Badges & Controls */}
        <div className="flex flex-wrap items-center gap-2 md:gap-3">
          {/* Privacy badge */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>{t('privacy_notice_badge')}</span>
          </div>

          {/* Mode indicator */}
          <div className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${
            processingMode === 'demo'
              ? 'bg-amber-50 text-amber-800 border-amber-200'
              : 'bg-blue-50 text-blue-800 border-blue-200'
          }`}>
            {processingMode === 'demo' ? t('simulated_demo_badge') : t('real_mode_badge')}
          </div>

          {/* Online/Offline status */}
          <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
            {isOnline ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                <span>{t('online')}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-rose-600" />
                <span>{t('offline_ready')}</span>
              </>
            )}
          </div>

          {/* 12-Language Selector */}
          <div className="relative inline-flex items-center">
            <Globe className="w-4 h-4 text-slate-500 absolute left-2 pointer-events-none" />
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value as SupportedLocale)}
              className="pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-800 shadow-sm hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors cursor-pointer"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>

          {/* View Switcher Button */}
          <div className="flex items-center rounded-lg bg-slate-200 p-0.5 text-xs font-semibold">
            <button
              onClick={() => onViewChange('citizen')}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md transition-all ${
                currentView === 'citizen'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>{t('citizen_mode')}</span>
            </button>
            <button
              onClick={() => onViewChange('operator')}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-md transition-all ${
                currentView === 'operator'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Monitor className="w-3.5 h-3.5" />
              <span>{t('operator_mode')}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
