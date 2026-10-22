import React from 'react';
import { X, Printer, AlertTriangle, FileCheck } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface SelfDeclarationModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicantName: string;
  expandedName: string;
  docAName: string;
  docBName: string;
}

export const SelfDeclarationModal: React.FC<SelfDeclarationModalProps> = ({
  isOpen,
  onClose,
  applicantName,
  expandedName,
  docAName,
  docBName,
}) => {
  const { t } = useTranslation();

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b pb-3">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-lg bg-brand-50 text-brand-700">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">{t('declaration_title')}</h3>
              <p className="text-xs text-rose-600 font-semibold flex items-center gap-1 mt-0.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{t('declaration_disclaimer')}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Declaration Content Form */}
        <div className="p-5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-xs leading-relaxed space-y-3 font-serif">
          <div className="text-center pb-2 border-b border-slate-300">
            <h4 className="font-bold uppercase tracking-wider text-sm">
              SELF-DECLARATION FORM (NAME VARIANT CONFIRMATION)
            </h4>
            <p className="text-[11px] text-slate-500 font-sans mt-0.5">
              Subject to physical verification at MeeSeva / CSC Service Centre
            </p>
          </div>

          <p>
            I, <strong>{expandedName || 'Applicant'}</strong>, hereby declare that the name appearing as{' '}
            <span className="font-bold underline">{applicantName}</span> in my {docAName || 'Primary Document'} and as{' '}
            <span className="font-bold underline">{expandedName}</span> in my {docBName || 'Secondary Document'} refer to
            one and the same individual, namely myself.
          </p>

          <p>
            The difference between the two names is solely due to the abbreviation / initial expansion of my family surname,
            and there is no intent of impersonation or misrepresentation.
          </p>

          <p>
            I understand that this pre-generated declaration is a voluntary draft template provided by the SevaDristi advisory
            system and is subject to the acceptance of the receiving government officer or Tahsildar authority.
          </p>

          <div className="pt-8 flex justify-between items-end font-sans">
            <div>
              <p className="text-[11px] text-slate-500">Date: {new Date().toLocaleDateString()}</p>
              <p className="text-[11px] text-slate-500">Place: Telangana State</p>
            </div>
            <div className="text-right">
              <div className="w-40 border-b border-slate-400 mb-1"></div>
              <p className="font-semibold text-slate-700">Signature of Applicant</p>
            </div>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-end space-x-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
          <button
            onClick={handlePrint}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-sm"
          >
            <Printer className="w-4 h-4" />
            <span>{t('print_declaration_btn')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
