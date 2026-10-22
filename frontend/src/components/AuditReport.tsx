import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Copy,
  Check,
  FileText,
  RotateCcw,
  Info,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';
import { AudioAdvisoryPlayer } from './AudioAdvisoryPlayer';
import { SelfDeclarationModal } from './SelfDeclarationModal';
import type { VerificationResponse } from '../types';

interface AuditReportProps {
  report: VerificationResponse;
  onResetSession: () => void;
  onNavigateToOperator: (qrPayload: string) => void;
}

export const AuditReport: React.FC<AuditReportProps> = ({
  report,
  onResetSession,
  onNavigateToOperator,
}) => {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [declarationModalOpen, setDeclarationModalOpen] = useState(false);

  const handleCopyQR = () => {
    if (report.qr_payload) {
      navigator.clipboard.writeText(report.qr_payload);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Determine traffic-light styles
  const isGreen = report.overall_status === 'NO_ISSUES_DETECTED';
  const isYellow = report.overall_status === 'NEEDS_REVIEW';
  const isRed = report.overall_status === 'ACTION_REQUIRED';

  const initialExpansionItem = report.field_comparisons.find(
    (fc) => fc.status === 'WARNING_INITIAL_EXPANSION'
  );

  // Combine advisories into one narrative for audio speech
  const speechNarrative = report.advisories
    .map((a) => `${a.title}. ${a.description} ${a.actionable_step}`)
    .join(' ');

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* 1. Traffic-Light Status Hero Banner */}
      <div
        className={`rounded-2xl p-6 border shadow-lg transition-all ${
          isGreen
            ? 'bg-gradient-to-br from-emerald-50 to-green-100/70 border-emerald-300'
            : isYellow
            ? 'bg-gradient-to-br from-amber-50 to-yellow-100/70 border-amber-300'
            : 'bg-gradient-to-br from-rose-50 to-red-100/70 border-rose-300'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div
              className={`p-3 rounded-2xl shadow-sm text-white shrink-0 ${
                isGreen ? 'bg-emerald-600' : isYellow ? 'bg-amber-600' : 'bg-rose-600'
              }`}
            >
              {isGreen && <CheckCircle className="w-8 h-8" />}
              {isYellow && <AlertTriangle className="w-8 h-8" />}
              {isRed && <AlertCircle className="w-8 h-8" />}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                    isGreen
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : isYellow
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-rose-100 text-rose-800 border-rose-300'
                  }`}
                >
                  {report.overall_status.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  Session: {report.session_id}
                </span>
              </div>

              <h2 className="text-xl font-black text-slate-900 mt-1">
                {isGreen
                  ? t('status_no_issues')
                  : isYellow
                  ? t('status_needs_review')
                  : t('status_action_required')}
              </h2>
              <p className="text-xs text-slate-600 mt-0.5">
                Evaluation for <strong>{report.scheme_name}</strong> (Rule ver: {report.rule_version})
              </p>
            </div>
          </div>

          {/* Spoken Advisories Button and Reset Action */}
          <div className="self-start md:self-center flex items-center gap-2">
            {speechNarrative && <AudioAdvisoryPlayer textToSpeak={speechNarrative} />}
            <button
              onClick={onResetSession}
              className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{t('reset_session_btn')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Actionable Advisories List */}
      {report.advisories.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <span>Actionable Pre-Verification Advisories ({report.advisories.length})</span>
          </h3>

          <div className="grid grid-cols-1 gap-3">
            {report.advisories.map((advisory) => (
              <div
                key={advisory.id}
                className={`rounded-xl p-4 border bg-white shadow-sm flex flex-col md:flex-row md:items-start justify-between gap-3 ${
                  advisory.severity === 'ERROR'
                    ? 'border-rose-200 bg-rose-50/20'
                    : 'border-amber-200 bg-amber-50/20'
                }`}
              >
                <div className="space-y-1 text-left">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        advisory.severity === 'ERROR'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {advisory.severity}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900">{advisory.title}</h4>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{advisory.description}</p>
                  <p className="text-xs font-semibold text-brand-800 pt-1 flex items-start gap-1">
                    <span className="text-slate-500 font-normal">{t('actionable_guidance')}</span>{' '}
                    {advisory.actionable_step}
                  </p>
                </div>

                {/* Initial Expansion Draft Trigger */}
                {advisory.id === 'INITIAL_EXPANSION' && initialExpansionItem && (
                  <button
                    onClick={() => setDeclarationModalOpen(true)}
                    className="self-start shrink-0 inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>{t('generate_declaration_btn')}</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Cross-Document Field Reconciliation Matrix */}
      {report.field_comparisons.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center justify-between">
            <span>{t('comparison_matrix_title')}</span>
            <span className="text-xs font-mono text-slate-500 lowercase">
              RapidFuzz & Indic Phonetic Matcher
            </span>
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px]">
                  <th className="py-2.5 px-3">Field</th>
                  <th className="py-2.5 px-3">Document A</th>
                  <th className="py-2.5 px-3">Document B</th>
                  <th className="py-2.5 px-3">Analysis & Metrics</th>
                  <th className="py-2.5 px-3">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.field_comparisons.map((fc, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-semibold text-slate-900 capitalize">
                      {fc.field_name.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-800">{fc.doc_a_val || 'N/A'}</div>
                      <div className="text-[10px] text-slate-400">{fc.doc_a_type}</div>
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-800">{fc.doc_b_val || 'N/A'}</div>
                      <div className="text-[10px] text-slate-400">{fc.doc_b_type}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-600 max-w-xs">
                      <div className="text-[11px] leading-relaxed mb-1">{fc.details.explanation}</div>
                      <div className="flex gap-2 text-[10px] font-mono text-slate-500">
                        <span>
                          {t('token_similarity')} {(fc.details.token_similarity * 100).toFixed(0)}%
                        </span>
                        <span>
                          {t('phonetic_similarity')} {(fc.details.phonetic_similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block px-2 py-1 rounded text-[10px] font-bold ${
                          fc.status === 'GREEN_MATCH'
                            ? 'bg-emerald-100 text-emerald-800'
                            : fc.status === 'WARNING_INITIAL_EXPANSION'
                            ? 'bg-amber-100 text-amber-800'
                            : fc.status === 'YELLOW_REVIEW'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {fc.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Signed Pre-Verification Summary QR & Operator Hand-off */}
      {report.qr_available && report.qr_payload && (
        <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-3 max-w-xl text-left">
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold">Signed Pre-Verification Summary QR</h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              This summary token contains only non-sensitive verification results and a cryptographically signed HMAC-SHA256 seal. No raw biometric or Aadhaar numbers are embedded.
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                onClick={handleCopyQR}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold border border-slate-700 text-slate-200 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied Token' : 'Copy Signed QR Token'}</span>
              </button>

              <button
                onClick={() => onNavigateToOperator(report.qr_payload!)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-xs font-bold text-white shadow-sm transition-colors"
              >
                <span>Test in CSC Operator View</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* QR Image Box */}
          {report.qr_data_url && (
            <div className="shrink-0 bg-white p-3 rounded-2xl shadow-md border border-slate-200 text-center">
              <img
                src={report.qr_data_url}
                alt="Pre-Verification Summary QR"
                className="w-36 h-36 mx-auto object-contain"
              />
              <span className="text-[10px] font-mono text-slate-500 block mt-1">
                Scan at MeeSeva Counter
              </span>
            </div>
          )}
        </div>
      )}

      {/* 5. Rule Source & Limitations Disclaimers */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-600 text-xs space-y-1 text-left">
        <div className="flex items-center space-x-1.5 font-semibold text-slate-800">
          <Info className="w-4 h-4 text-slate-500" />
          <span>{t('rule_provenance')} {report.rule_source}</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Disclaimer: SevaDristi is a citizen assistance tool designed for hackathon demonstration. It does not issue official government approvals or legal exemptions.
        </p>
      </div>

      {/* Self-Declaration Modal */}
      {initialExpansionItem && (
        <SelfDeclarationModal
          isOpen={declarationModalOpen}
          onClose={() => setDeclarationModalOpen(false)}
          applicantName={initialExpansionItem.doc_a_val || 'S. RAKESH'}
          expandedName={initialExpansionItem.doc_b_val || 'SARIPILLY RAKESH'}
          docAName={initialExpansionItem.doc_a_type}
          docBName={initialExpansionItem.doc_b_type}
        />
      )}
    </div>
  );
};
