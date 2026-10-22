import React, { useRef } from 'react';
import { Upload, Camera, Trash2, RotateCcw, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';
import type { DocumentAnalysis } from '../types';

interface DocumentUploaderProps {
  files: File[];
  analyzedDocs: DocumentAnalysis[];
  onAddFiles: (newFiles: File[]) => void;
  onRemoveDoc: (index: number) => void;
  onResetSession: () => void;
  isLoading: boolean;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  files,
  analyzedDocs,
  onAddFiles,
  onRemoveDoc,
  onResetSession,
  isLoading,
}) => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = Array.from(e.target.files);
      onAddFiles(selected);
    }
  };

  const hasDocs = files.length > 0 || analyzedDocs.length > 0;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            {t('upload_instruction')}
          </h3>
          <p className="text-xs text-slate-500">
            Aadhaar, Ration Card, Income/Caste Certificates or Passbook. All processed strictly in RAM.
          </p>
        </div>

        {hasDocs && (
          <button
            onClick={onResetSession}
            className="self-start sm:self-auto inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-semibold transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>{t('reset_session_btn')}</span>
          </button>
        )}
      </div>

      {/* Hidden Inputs */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />
      <input
        type="file"
        ref={cameraInputRef}
        onChange={handleFileChange}
        accept="image/*"
        capture="environment"
        className="hidden"
      />

      {/* Upload Dropzone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-brand-50/20 group"
      >
        <div className="flex flex-col items-center space-y-2">
          <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center group-hover:scale-105 transition-transform">
            <Upload className="w-6 h-6" />
          </div>
          <div className="text-xs font-medium text-slate-700">
            <span className="font-bold text-brand-700 hover:underline">{t('drag_drop_hint')}</span>
          </div>
          <p className="text-[11px] text-slate-400">Max size 10MB per document image</p>

          <div className="flex items-center gap-2 pt-2">
            <button
              type="button"
              disabled={isLoading}
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-100 flex items-center gap-1.5 disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{t('upload_btn')}</span>
            </button>
            <button
              type="button"
              disabled={isLoading}
              onClick={(e) => {
                e.stopPropagation();
                cameraInputRef.current?.click();
              }}
              className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-semibold shadow-sm hover:bg-brand-700 flex items-center gap-1.5 disabled:opacity-50"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>{t('camera_btn')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Uploaded / Analyzed Document Cards */}
      {analyzedDocs.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Processed Documents ({analyzedDocs.length})
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {analyzedDocs.map((doc, idx) => (
              <div
                key={doc.id || idx}
                className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm space-y-2 text-left"
              >
                {/* Title row */}
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {doc.doc_type}
                    </span>
                    <h5 className="text-xs font-bold text-slate-900 mt-1">
                      {doc.doc_name || doc.doc_type}
                    </h5>
                  </div>
                  <button
                    onClick={() => onRemoveDoc(idx)}
                    className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    title={t('remove_btn')}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Quality Badges */}
                <div className="flex flex-wrap gap-1.5 text-[11px]">
                  {doc.is_blurred ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                      <AlertTriangle className="w-3 h-3 text-amber-600" />
                      <span>{t('sharpness_score')} {doc.blur_score.toFixed(1)} (Low)</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      <span>Sharp ({doc.blur_score.toFixed(1)})</span>
                    </span>
                  )}

                  {doc.has_glare ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                      <AlertTriangle className="w-3 h-3 text-amber-600" />
                      <span>{t('glare_score')} {(doc.glare_ratio * 100).toFixed(1)}%</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                      <span>Glare: {(doc.glare_ratio * 100).toFixed(1)}%</span>
                    </span>
                  )}

                  {doc.crop_applied && (
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                      {t('crop_applied')}
                    </span>
                  )}
                </div>

                {/* Extracted Fields Preview */}
                <div className="bg-slate-50 rounded-lg p-2.5 text-xs space-y-1 border border-slate-100">
                  {doc.extracted_fields.full_name && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Name:</span>
                      <span className="font-bold text-slate-800">{doc.extracted_fields.full_name}</span>
                    </div>
                  )}
                  {doc.extracted_fields.dob && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">DOB:</span>
                      <span className="font-medium text-slate-700">{doc.extracted_fields.dob}</span>
                    </div>
                  )}
                  {doc.extracted_fields.issue_date && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Issue Date:</span>
                      <span className="font-medium text-slate-700">{doc.extracted_fields.issue_date}</span>
                    </div>
                  )}
                  {doc.extracted_fields.annual_income_inr && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Annual Income:</span>
                      <span className="font-medium text-slate-700">₹{doc.extracted_fields.annual_income_inr.toLocaleString()}</span>
                    </div>
                  )}
                  {doc.extracted_fields.id_reference && (
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Masked ID:</span>
                      <span className="font-mono text-[11px] font-bold text-slate-700 bg-white px-1.5 py-0.5 rounded border border-slate-200 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3 text-brand-600" />
                        {doc.extracted_fields.id_reference}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
