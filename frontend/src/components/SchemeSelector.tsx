import React from 'react';
import { Award, Users, Sprout, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';
import type { SchemeInfo } from '../types';

interface SchemeSelectorProps {
  schemes: SchemeInfo[];
  selectedSchemeId: string;
  onSelectScheme: (schemeId: string) => void;
}

export const SchemeSelector: React.FC<SchemeSelectorProps> = ({
  schemes,
  selectedSchemeId,
  onSelectScheme,
}) => {
  const { t, locale } = useTranslation();

  const getSchemeIcon = (id: string) => {
    switch (id) {
      case 'epass_scholarship':
        return <Award className="w-5 h-5 text-indigo-600" />;
      case 'aasara_pension':
        return <Users className="w-5 h-5 text-emerald-600" />;
      case 'rythu_bharosa':
        return <Sprout className="w-5 h-5 text-amber-600" />;
      default:
        return <FileText className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <span>{t('select_scheme_title')}</span>
          <span className="text-xs font-normal text-slate-500 lowercase">
            ({schemes.length} available)
          </span>
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {schemes.map((scheme) => {
          const isSelected = scheme.id === selectedSchemeId;
          const isVerified = scheme.verification_state === 'VERIFIED';
          const title = locale === 'te-IN' && scheme.display_name_te ? scheme.display_name_te : scheme.display_name;

          return (
            <div
              key={scheme.id}
              onClick={() => onSelectScheme(scheme.id)}
              className={`relative rounded-xl p-4 transition-all cursor-pointer border text-left ${
                isSelected
                  ? 'bg-white border-brand-500 shadow-md ring-2 ring-brand-500/20'
                  : 'bg-white/70 hover:bg-white border-slate-200 hover:border-slate-300 shadow-sm'
              }`}
            >
              {/* Header row */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    {getSchemeIcon(scheme.id)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 leading-tight">
                      {title}
                    </h3>
                    <span className="text-[11px] text-slate-500">{scheme.jurisdiction}</span>
                  </div>
                </div>

                {/* State Tag */}
                {isVerified ? (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{t('verified_policy')}</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                    <AlertTriangle className="w-3 h-3" />
                    <span>{t('draft_demo_policy')}</span>
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-xs text-slate-600 line-clamp-2 mb-3">
                {scheme.description}
              </p>

              {/* Required Documents Checklist */}
              <div className="pt-2 border-t border-slate-100">
                <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                  {t('required_docs_label')}
                </span>
                <div className="flex flex-wrap gap-1">
                  {scheme.required_documents.map((docType) => (
                    <span
                      key={docType}
                      className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200"
                    >
                      {docType.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
