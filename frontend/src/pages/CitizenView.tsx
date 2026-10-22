import React, { useState, useEffect } from 'react';
import { SchemeSelector } from '../components/SchemeSelector';
import { PresetSelector } from '../components/PresetSelector';
import { DocumentUploader } from '../components/DocumentUploader';
import { AuditReport } from '../components/AuditReport';
import { WageSavedDashboard } from '../components/WageSavedDashboard';
import { fetchSchemes, verifyDocuments } from '../services/api';
import { useTranslation } from '../hooks/useTranslation';
import type { SchemeInfo, VerificationResponse, DocumentAnalysis } from '../types';

interface CitizenViewProps {
  onNavigateToOperator: (qrPayload: string) => void;
  setProcessingMode: (mode: 'real' | 'demo') => void;
}

export const CitizenView: React.FC<CitizenViewProps> = ({
  onNavigateToOperator,
  setProcessingMode,
}) => {
  const { locale } = useTranslation();
  const [schemes, setSchemes] = useState<SchemeInfo[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>('epass_scholarship');
  const [files, setFiles] = useState<File[]>([]);
  const [analyzedDocs, setAnalyzedDocs] = useState<DocumentAnalysis[]>([]);
  const [report, setReport] = useState<VerificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Simulated metrics tracking
  const [casesCount, setCasesCount] = useState<number>(3);
  const [issuesPreempted, setIssuesPreempted] = useState<number>(5);
  const [visitsAvoided, setVisitsAvoided] = useState<number>(3);

  useEffect(() => {
    fetchSchemes()
      .then((data) => {
        setSchemes(data);
        if (data.length > 0) {
          setSelectedSchemeId(data[0].id);
        }
      })
      .catch((err) => {
        console.error('Failed to load schemes', err);
      });
  }, []);

  const handleRunPreset = async (presetId: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    setProcessingMode('demo');

    try {
      const res = await verifyDocuments([], selectedSchemeId, locale, presetId);
      setReport(res);
      setAnalyzedDocs(res.documents);
      setCasesCount((prev) => prev + 1);
      setIssuesPreempted((prev) => prev + res.quality_issues.length + res.scheme_issues.length);
      if (res.overall_status !== 'NO_ISSUES_DETECTED') {
        setVisitsAvoided((prev) => prev + 1);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Preset execution failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddFiles = async (newFiles: File[]) => {
    const updated = [...files, ...newFiles];
    setFiles(updated);
    setIsLoading(true);
    setErrorMsg(null);
    setProcessingMode('real');

    try {
      const res = await verifyDocuments(updated, selectedSchemeId, locale);
      setReport(res);
      setAnalyzedDocs(res.documents);
      setCasesCount((prev) => prev + 1);
      setIssuesPreempted((prev) => prev + res.quality_issues.length + res.scheme_issues.length);
    } catch (err: any) {
      setErrorMsg(err.message || 'Document verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveDoc = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    const updatedAnalyzed = analyzedDocs.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    setAnalyzedDocs(updatedAnalyzed);
    if (updatedFiles.length === 0 && updatedAnalyzed.length === 0) {
      setReport(null);
    }
  };

  const handleResetSession = () => {
    setFiles([]);
    setAnalyzedDocs([]);
    setReport(null);
    setErrorMsg(null);
    setProcessingMode('demo');
  };

  return (
    <div className="space-y-6">
      {/* 1. Scheme Selector Cards */}
      <SchemeSelector
        schemes={schemes}
        selectedSchemeId={selectedSchemeId}
        onSelectScheme={(id) => {
          setSelectedSchemeId(id);
          // If docs are present, re-verify
          if (files.length > 0) {
            verifyDocuments(files, id, locale).then((res) => setReport(res));
          }
        }}
      />

      {/* 2. Jury Demo Presets */}
      <PresetSelector onRunPreset={handleRunPreset} isLoading={isLoading} />

      {/* 3. Document Uploader */}
      <DocumentUploader
        files={files}
        analyzedDocs={analyzedDocs}
        onAddFiles={handleAddFiles}
        onRemoveDoc={handleRemoveDoc}
        onResetSession={handleResetSession}
        isLoading={isLoading}
      />

      {/* Error alert if any */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold text-left">
          {errorMsg}
        </div>
      )}

      {/* Loading state indicator */}
      {isLoading && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 text-center space-y-2 shadow-sm animate-pulse">
          <div className="w-8 h-8 rounded-full border-2 border-brand-600 border-t-transparent animate-spin mx-auto"></div>
          <p className="text-xs font-bold text-slate-800">
            Running In-Memory Quality Gate, Indic Phonetic Reconciliation & Policy Checks...
          </p>
        </div>
      )}

      {/* 4. Verification Audit Report */}
      {report && (
        <AuditReport
          report={report}
          onResetSession={handleResetSession}
          onNavigateToOperator={onNavigateToOperator}
        />
      )}

      {/* 5. Wage-Saved Simulated Impact Dashboard */}
      <WageSavedDashboard
        casesProcessed={casesCount}
        issuesPreempted={issuesPreempted}
        repeatVisitsAvoided={visitsAvoided}
      />
    </div>
  );
};
