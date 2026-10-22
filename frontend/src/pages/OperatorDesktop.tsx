import React, { useState, useEffect } from 'react';
import { Monitor, QrCode, ShieldCheck, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react';
import { decodeQrPayload } from '../services/api';
import { useTranslation } from '../hooks/useTranslation';
import type { DecodedQRResponse } from '../types';

interface OperatorDesktopProps {
  initialQrPayload?: string;
  onBackToCitizen: () => void;
}

export const OperatorDesktop: React.FC<OperatorDesktopProps> = ({
  initialQrPayload = '',
  onBackToCitizen,
}) => {
  const { t } = useTranslation();
  const [tokenInput, setTokenInput] = useState<string>(initialQrPayload);
  const [decoded, setDecoded] = useState<DecodedQRResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (initialQrPayload) {
      handleDecode(initialQrPayload);
    }
  }, [initialQrPayload]);

  const handleDecode = async (tokenToVerify?: string) => {
    const raw = tokenToVerify || tokenInput;
    if (!raw.trim()) return;

    setIsLoading(true);

    try {
      const res = await decodeQrPayload(raw.trim());
      setDecoded(res);
    } catch (err) {
      console.error(err);
      setDecoded({
        valid_signature: false,
        not_expired: false,
        verification_scope: 'NONE',
        verified_fields: {},
        warnings: ['Failed to verify token with backend service.']
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulateTamper = () => {
    if (!tokenInput) return;
    const tampered = tokenInput.slice(0, -6) + 'abc123';
    setTokenInput(tampered);
    handleDecode(tampered);
  };

  const verifiedFields = decoded?.valid_signature ? decoded.verified_fields : {};

  return (
    <div className="space-y-6 text-left">
      {/* Operator Title Bar */}
      <div className="bg-slate-900 rounded-2xl p-5 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-tsblue-700 text-white">
            <Monitor className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">{t('operator_title')}</h2>
            <p className="text-xs text-slate-400">
              Form Auto-Fill with Cryptographic HMAC-SHA256 Pre-Verification Token
            </p>
          </div>
        </div>

        <button
          onClick={onBackToCitizen}
          className="self-start md:self-auto inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Citizen Assistant</span>
        </button>
      </div>

      {/* QR Input & Verification Box */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <QrCode className="w-5 h-5 text-brand-600" />
            <h3 className="text-sm font-bold text-slate-900">{t('scan_qr_hint')}</h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Payload.Signature</span>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="Paste Pre-Verification Summary token here (e.g. eyJ2ZXIi...)"
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            onClick={() => handleDecode()}
            disabled={isLoading || !tokenInput}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-sm transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Verifying...' : t('decode_qr_btn')}
          </button>
          <button
            onClick={handleSimulateTamper}
            disabled={isLoading || !tokenInput}
            className="px-3 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold transition-colors"
            title="Simulate altered token payload to test rejection"
          >
            Tamper Test
          </button>
        </div>

        {/* Verification Status Banner */}
        {decoded && (
          <div
            className={`p-4 rounded-xl border flex items-start space-x-3 ${
              decoded.valid_signature && decoded.not_expired
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {decoded.valid_signature && decoded.not_expired ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-600" />
              )}
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm">
                  {decoded.valid_signature && decoded.not_expired
                    ? t('verified_seal')
                    : !decoded.valid_signature
                    ? t('tampered_warning')
                    : t('expired_warning')}
                </span>
                {decoded.issuer && (
                  <span className="px-2 py-0.5 rounded bg-white/70 text-[10px] font-mono border">
                    Issuer: {decoded.issuer}
                  </span>
                )}
              </div>

              <p className="text-slate-600">{decoded.verification_scope}</p>

              {decoded.warnings.length > 0 && (
                <div className="pt-1 text-rose-700 font-semibold">
                  Warnings: {decoded.warnings.join('; ')}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* MeeSeva Application Form Simulator */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Government Welfare Application Form Simulation
            </h3>
            <p className="text-xs text-slate-500">
              {decoded?.valid_signature
                ? t('autofilled_notice')
                : 'Fields locked or manual until a cryptographically verified token is presented.'}
            </p>
          </div>
          <span className="text-[10px] uppercase font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
            Form TS-MeeSeva-01
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Field 1: Name */}
          <div className="space-y-1">
            <label className="font-bold text-slate-700 flex items-center justify-between">
              <span>{t('applicant_name')}</span>
              {verifiedFields.nam ? (
                <span className="text-[10px] text-emerald-700 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Auto-filled
                </span>
              ) : (
                <span className="text-[10px] text-slate-400">Manual Entry Required</span>
              )}
            </label>
            <input
              type="text"
              readOnly
              value={verifiedFields.nam || ''}
              placeholder="Requires Verified QR Token"
              className={`w-full px-3 py-2 rounded-xl border text-xs font-semibold ${
                verifiedFields.nam
                  ? 'bg-emerald-50/50 border-emerald-300 text-slate-900'
                  : 'bg-slate-100 border-slate-200 text-slate-400'
              }`}
            />
          </div>

          {/* Field 2: Scheme ID */}
          <div className="space-y-1">
            <label className="font-bold text-slate-700">Scheme Code / Identifier:</label>
            <input
              type="text"
              readOnly
              value={decoded?.scheme_id || ''}
              placeholder="e.g. epass_scholarship"
              className="w-full px-3 py-2 rounded-xl border bg-slate-100 border-slate-200 text-slate-700 text-xs font-mono"
            />
          </div>

          {/* Field 3: DOB */}
          <div className="space-y-1">
            <label className="font-bold text-slate-700 flex items-center justify-between">
              <span>{t('dob')}</span>
              {verifiedFields.dob_yr ? (
                <span className="text-[10px] text-emerald-700 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Year Verified
                </span>
              ) : (
                <span className="text-[10px] text-slate-400">Requires Manual Check</span>
              )}
            </label>
            <input
              type="text"
              readOnly
              value={verifiedFields.dob_yr || ''}
              placeholder="YYYY"
              className={`w-full px-3 py-2 rounded-xl border text-xs font-semibold ${
                verifiedFields.dob_yr
                  ? 'bg-emerald-50/50 border-emerald-300 text-slate-900'
                  : 'bg-slate-100 border-slate-200 text-slate-400'
              }`}
            />
          </div>

          {/* Field 4: Postal PIN Code */}
          <div className="space-y-1">
            <label className="font-bold text-slate-700 flex items-center justify-between">
              <span>{t('pincode')}</span>
              {verifiedFields.pin ? (
                <span className="text-[10px] text-emerald-700 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Auto-filled
                </span>
              ) : (
                <span className="text-[10px] text-slate-400">Requires Manual Check</span>
              )}
            </label>
            <input
              type="text"
              readOnly
              value={verifiedFields.pin || ''}
              placeholder="500032"
              className={`w-full px-3 py-2 rounded-xl border text-xs font-semibold ${
                verifiedFields.pin
                  ? 'bg-emerald-50/50 border-emerald-300 text-slate-900'
                  : 'bg-slate-100 border-slate-200 text-slate-400'
              }`}
            />
          </div>

          {/* Field 5: Pre-Verification Status */}
          <div className="space-y-1 md:col-span-2">
            <label className="font-bold text-slate-700">{t('status_label')}</label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                readOnly
                value={decoded?.pre_verification_status || 'NOT VERIFIED'}
                className="w-full px-3 py-2 rounded-xl border bg-slate-100 border-slate-200 text-slate-800 text-xs font-mono font-bold"
              />
              <span className="text-[11px] text-slate-500 whitespace-nowrap">
                Ref: {decoded?.session_ref || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="button"
            className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 shadow-md transition-all flex items-center gap-2"
          >
            <span>Proceed to MeeSeva Biometric Ingestion</span>
          </button>
        </div>
      </div>
    </div>
  );
};
