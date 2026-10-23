import React, { useState, useEffect } from 'react';
import { SchemeSelector } from '../components/SchemeSelector';
import { DocumentChecklist } from '../components/DocumentChecklist';
import { RealUploader } from '../components/RealUploader';
import { NameReview } from '../components/NameReview';
import { AuditReport } from '../components/AuditReport';
import { OnboardingModal } from '../components/OnboardingModal';
import { fetchSchemes, verifyDocuments, extractSingleDoc } from '../services/api';
import { useTranslation } from '../hooks/useTranslation';
import type { SchemeInfo, VerificationResponse } from '../types';
import { ArrowRight, ShieldCheck, RefreshCw, AlertCircle, HelpCircle } from 'lucide-react';

interface CitizenViewProps {
  onNavigateToOperator: (qrPayload: string) => void;
  setProcessingMode: (mode: 'real' | 'demo') => void;
}

interface UploadedDocState {
  file: File;
  qualityScore: number;
  isBlurred: boolean;
  hasGlare: boolean;
  extractedName?: string | null;
  confidence: number;
}

export const CitizenView: React.FC<CitizenViewProps> = ({
  onNavigateToOperator,
  setProcessingMode,
}) => {
  const { locale } = useTranslation();
  const [schemes, setSchemes] = useState<SchemeInfo[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>('epass_scholarship');
  const [uploadedDocs, setUploadedDocs] = useState<Record<string, UploadedDocState>>({});
  const [userEditedNames, setUserEditedNames] = useState<Record<string, string>>({});
  const [report, setReport] = useState<VerificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);

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

  const activeScheme = schemes.find((s) => s.id === selectedSchemeId) || null;

  // Handle document capture / selection
  const handleDocSelected = async (
    docType: string,
    file: File,
    qualityScore: number,
    isBlurred: boolean,
    hasGlare: boolean
  ) => {
    // Record basic upload state
    const newState: UploadedDocState = {
      file,
      qualityScore,
      isBlurred,
      hasGlare,
      extractedName: null,
      confidence: 0.8
    };

    setUploadedDocs((prev) => ({ ...prev, [docType]: newState }));
    setErrorMsg(null);

    // Call real OCR single extraction in background
    try {
      const res = await extractSingleDoc(file, docType);
      setUploadedDocs((prev) => ({
        ...prev,
        [docType]: {
          ...prev[docType],
          extractedName: res.extracted_name,
          confidence: res.confidence
        }
      }));
    } catch (e) {
      console.warn('Single doc OCR extraction note:', e);
    }
  };

  const handleRemoveDoc = (docType: string) => {
    setUploadedDocs((prev) => {
      const copy = { ...prev };
      delete copy[docType];
      return copy;
    });
    setUserEditedNames((prev) => {
      const copy = { ...prev };
      delete copy[docType];
      return copy;
    });
    setReport(null);
  };

  const handleNamesUpdated = (updated: Record<string, string>) => {
    setUserEditedNames(updated);
  };

  // Full verification submission
  const handleVerifyAll = async () => {
    const docEntries = Object.entries(uploadedDocs);
    if (docEntries.length === 0) {
      setErrorMsg(
        locale === 'te-IN'
          ? 'దయచేసి కనీసం ఒక పత్రాన్ని అప్‌లోడ్ చేయండి.'
          : 'Please upload at least one document to verify.'
      );
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setProcessingMode('real');

    const filesList: File[] = [];
    const docTypesList: string[] = [];
    for (const [docType, data] of docEntries) {
      filesList.push(data.file);
      docTypesList.push(docType);
    }

    try {
      const res = await verifyDocuments(
        filesList,
        selectedSchemeId,
        locale,
        userEditedNames,
        docTypesList
      );
      setReport(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification failed. Please check files and retry.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSession = () => {
    setUploadedDocs({});
    setUserEditedNames({});
    setReport(null);
    setErrorMsg(null);
  };

  // Prepare checklist tracking
  const uploadedTypesSet = new Set(Object.keys(uploadedDocs));
  const blurryTypesSet = new Set(
    Object.entries(uploadedDocs)
      .filter(([_, d]) => d.isBlurred)
      .map(([type]) => type)
  );

  // Prepare names for NameReview
  const namesForReview = Object.entries(uploadedDocs)
    .filter(([_, d]) => d.extractedName)
    .map(([docType, d]) => ({
      docType,
      docLabel: docType.replace('_', ' '),
      extractedName: d.extractedName!,
      confidence: d.confidence
    }));

  return (
    <div className="space-y-6">
      {/* Onboarding Trigger & Scheme Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            {locale === 'te-IN' ? 'పత్రాల పూర్వ-పరిశీలన' : 'Citizen Document Pre-Verification'}
          </h2>
          <p className="text-xs text-slate-500">
            {locale === 'te-IN'
              ? 'మీసేవా కేంద్రానికి వెళ్ళేముందు పత్రాల నాణ్యత, పేర్లు మరియు చెల్లుబాటును తనిఖీ చేయండి.'
              : 'Pre-screen documents for blur, glare, and transliteration discrepancies before visiting MeeSeva.'}
          </p>
        </div>

        <button
          onClick={() => setShowOnboarding(true)}
          className="self-start sm:self-center px-3 py-1.5 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold flex items-center gap-1.5 transition"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          <span>{locale === 'te-IN' ? 'ఎలా పనిచేస్తుంది?' : 'How it works'}</span>
        </button>
      </div>

      {/* Scheme Selection Cards */}
      <SchemeSelector
        schemes={schemes}
        selectedSchemeId={selectedSchemeId}
        onSelectScheme={(id) => {
          setSelectedSchemeId(id);
          setReport(null);
        }}
      />

      {/* Required Documents Checklist */}
      <DocumentChecklist
        scheme={activeScheme}
        uploadedTypes={uploadedTypesSet}
        blurryTypes={blurryTypesSet}
      />

      {/* Document Upload Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            {locale === 'te-IN' ? 'పత్రాల ఫోటోలు తీయండి / అప్‌లోడ్ చేయండి' : 'Capture or Upload Documents'}
          </h3>
          <span className="text-xs text-slate-400">
            {Object.keys(uploadedDocs).length} {locale === 'te-IN' ? 'జతచేయబడ్డాయి' : 'attached'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(activeScheme?.required_documents || ['IDENTITY_CARD', 'INCOME_CERT']).map((docType) => (
            <RealUploader
              key={docType}
              docType={docType}
              docLabel={docType.replace('_', ' ')}
              existingFile={uploadedDocs[docType]?.file || null}
              onFileSelected={(file, qualityScore, isBlurred, hasGlare) =>
                handleDocSelected(docType, file, qualityScore, isBlurred, hasGlare)
              }
              onRemove={() => handleRemoveDoc(docType)}
            />
          ))}
        </div>
      </div>

      {/* Extracted Names Review & Editing Card */}
      {namesForReview.length > 0 && (
        <NameReview
          docNames={namesForReview}
          onNamesUpdated={handleNamesUpdated}
        />
      )}

      {/* Verify Action Button */}
      {Object.keys(uploadedDocs).length > 0 && !report && (
        <div className="pt-2 text-center">
          <button
            onClick={handleVerifyAll}
            disabled={isLoading}
            className="w-full sm:w-auto px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-lg flex items-center justify-center gap-2 mx-auto transition disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>{locale === 'te-IN' ? 'పరిశీలన జరుగుతోంది...' : 'Verifying with Vision & OCR Gate...'}</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-5 h-5" />
                <span>
                  {locale === 'te-IN'
                    ? 'పూర్వ-పరిశీలన చేయండి & QR టోకెన్ పొందండి'
                    : 'Verify Documents & Generate Signed QR Token'}
                </span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Notice */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Verification Audit Report */}
      {report && (
        <AuditReport
          report={report}
          onResetSession={handleResetSession}
          onNavigateToOperator={onNavigateToOperator}
        />
      )}

      {/* Onboarding Tutorial Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
      />
    </div>
  );
};
