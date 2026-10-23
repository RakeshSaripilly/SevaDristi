import { CheckCircle2, AlertCircle, Clock, FileText } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';
import type { SchemeInfo } from '../types';

interface DocumentChecklistProps {
  scheme: SchemeInfo | null;
  uploadedTypes: Set<string>;
  blurryTypes: Set<string>;
}

const DOC_TYPE_LABELS: Record<string, { en: string; te: string; tip: string }> = {
  IDENTITY_CARD: {
    en: 'Aadhaar / Identity Card',
    te: 'ఆధార్ కార్డు / గుర్తింపు కార్డు',
    tip: 'Make sure full name and date of birth are clearly readable.'
  },
  INCOME_CERT: {
    en: 'Income Certificate',
    te: 'ఆదాయ ధృవీకరణ పత్రం',
    tip: 'Must be issued by Tahsildar within the past 12 months.'
  },
  CASTE_CERT: {
    en: 'Caste / Community Certificate',
    te: 'కుల ధృవీకరణ పత్రం',
    tip: 'Permanent community certificate issued by Revenue Department.'
  },
  RATION_CARD: {
    en: 'Food Security / Ration Card',
    te: 'రేషన్ కార్డు / ఆహార భద్రత కార్డు',
    tip: 'Front and family member listing page.'
  },
  BANK_PASSBOOK: {
    en: 'Bank Account Passbook',
    te: 'బ్యాంక్ పాస్ పుస్తకం',
    tip: 'Account number, IFSC code, and branch stamp must be visible.'
  },
  LAND_PASSBOOK: {
    en: 'Pattadar Passbook / Land Document',
    te: 'పట్టాదారు పాస్ పుస్తకం / భూమి పత్రం',
    tip: 'Katha number and survey number page.'
  }
};

export const DocumentChecklist: React.FC<DocumentChecklistProps> = ({
  scheme,
  uploadedTypes,
  blurryTypes,
}) => {
  const { locale } = useTranslation();

  if (!scheme) return null;

  const required = scheme.required_documents || [];
  const totalCount = required.length;
  const readyCount = required.filter(
    (t) => uploadedTypes.has(t) && !blurryTypes.has(t)
  ).length;
  const progressPercent = totalCount > 0 ? Math.round((readyCount / totalCount) * 100) : 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            {locale === 'te-IN' ? 'అవసరమైన పత్రాల జాబితా' : 'Required Documents Checklist'}
          </h3>
          <p className="text-xs text-slate-500">
            {scheme.display_name} ({locale === 'te-IN' ? 'పథకానికి' : 'Scheme'})
          </p>
        </div>

        {/* Progress Badge */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-600 font-medium">
            {readyCount} / {totalCount} {locale === 'te-IN' ? 'సిద్ధంగా ఉన్నాయి' : 'Ready'}
          </span>
          <div className="w-20 bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                progressPercent === 100 ? 'bg-emerald-500' : 'bg-indigo-600'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Checklist items */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {required.map((docType) => {
          const isUploaded = uploadedTypes.has(docType);
          const isBlurry = blurryTypes.has(docType);
          const info = DOC_TYPE_LABELS[docType] || {
            en: docType.replace('_', ' '),
            te: docType.replace('_', ' '),
            tip: 'Standard government certificate.'
          };

          let statusBadge = (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              <Clock className="w-3 h-3" />
              {locale === 'te-IN' ? 'పెండింగ్' : 'Pending'}
            </span>
          );

          if (isUploaded && !isBlurry) {
            statusBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                {locale === 'te-IN' ? 'సిద్ధం' : 'Ready'}
              </span>
            );
          } else if (isUploaded && isBlurry) {
            statusBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                <AlertCircle className="w-3 h-3 text-amber-600" />
                {locale === 'te-IN' ? 'అస్పష్టం (మళ్ళీ తీయండి)' : 'Needs Retake'}
              </span>
            );
          }

          return (
            <div
              key={docType}
              className={`p-3 rounded-lg border transition ${
                isUploaded && !isBlurry
                  ? 'border-emerald-200 bg-emerald-50/20'
                  : isUploaded && isBlurry
                  ? 'border-amber-200 bg-amber-50/20'
                  : 'border-slate-200 bg-slate-50/40'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-xs font-semibold text-slate-800">
                    {locale === 'te-IN' ? info.te : info.en}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">{info.tip}</p>
                </div>
                {statusBadge}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
