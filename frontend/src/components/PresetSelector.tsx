import React from 'react';
import { Sparkles, AlertCircle, AlertTriangle, CheckCircle, Eye } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface PresetSelectorProps {
  onRunPreset: (presetId: string) => void;
  isLoading: boolean;
}

export const PresetSelector: React.FC<PresetSelectorProps> = ({ onRunPreset, isLoading }) => {
  const { t } = useTranslation();

  const presets = [
    {
      id: 'preset_1_red',
      label: t('preset_1_label'),
      badge: 'RED ISSUE',
      badgeColor: 'bg-red-100 text-red-800 border-red-200',
      description: 'S. RAKESH vs SARIPILLY vs KONDAPALLI, Expired Income Cert (>1 yr), Blurred Passbook.',
      icon: <AlertCircle className="w-4 h-4 text-red-600" />,
      borderHover: 'hover:border-red-400',
    },
    {
      id: 'preset_2_yellow',
      label: t('preset_2_label'),
      badge: 'YELLOW REVIEW',
      badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
      description: 'SARIPILLY vs SARIPILLI (Phonetics) & S. RAKESH (Initial expansion advisory).',
      icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
      borderHover: 'hover:border-amber-400',
    },
    {
      id: 'preset_3_green',
      label: t('preset_3_label'),
      badge: 'GREEN READY',
      badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      description: 'SARIPILLY RAKESH consistent across all 4 documents. Sharpness high, valid dates.',
      icon: <CheckCircle className="w-4 h-4 text-emerald-600" />,
      borderHover: 'hover:border-emerald-400',
    },
    {
      id: 'preset_4_glare_seal',
      label: t('preset_4_label'),
      badge: 'QUALITY REVIEW',
      badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
      description: '15.2% Glare threshold exceeded; automated heuristic seal not confirmed.',
      icon: <Eye className="w-4 h-4 text-blue-600" />,
      borderHover: 'hover:border-blue-400',
    },
  ];

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-5 text-white shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wide uppercase">{t('jury_presets_title')}</h3>
            <p className="text-xs text-slate-400 font-normal">
              Click any scenario to immediately evaluate simulated document credentials.
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300">
          Synthetic Records
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {presets.map((p) => (
          <button
            key={p.id}
            disabled={isLoading}
            onClick={() => onRunPreset(p.id)}
            className={`group text-left p-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/90 border border-slate-700 transition-all flex flex-col justify-between ${p.borderHover} disabled:opacity-50`}
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${p.badgeColor}`}>
                  {p.badge}
                </span>
                {p.icon}
              </div>
              <h4 className="text-xs font-bold text-white group-hover:text-brand-300 transition-colors line-clamp-1 mb-1">
                {p.label}
              </h4>
              <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">
                {p.description}
              </p>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-white font-medium">
              <span>{t('run_preset_btn')}</span>
              <span className="text-brand-400">&rarr;</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
