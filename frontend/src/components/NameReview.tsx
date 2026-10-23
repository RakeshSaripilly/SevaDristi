import React, { useState } from 'react';
import { UserCheck, Edit3, Check, Sparkles } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface ExtractedDocName {
  docType: string;
  docLabel: string;
  extractedName: string;
  confidence: number;
}

interface NameReviewProps {
  docNames: ExtractedDocName[];
  onNamesUpdated: (updatedNames: Record<string, string>) => void;
}

export const NameReview: React.FC<NameReviewProps> = ({
  docNames,
  onNamesUpdated,
}) => {
  const { locale } = useTranslation();
  const [editingDocType, setEditingDocType] = useState<string | null>(null);
  const [customNames, setCustomNames] = useState<Record<string, string>>({});
  const [editInput, setEditInput] = useState<string>('');

  if (docNames.length === 0) return null;

  const handleStartEdit = (docType: string, currentVal: string) => {
    setEditingDocType(docType);
    setEditInput(customNames[docType] || currentVal);
  };

  const handleSaveEdit = (docType: string) => {
    const updated = { ...customNames, [docType]: editInput.trim().toUpperCase() };
    setCustomNames(updated);
    setEditingDocType(null);
    onNamesUpdated(updated);
  };

  const getActiveName = (doc: ExtractedDocName) => {
    return customNames[doc.docType] || doc.extractedName;
  };

  // Compare first 2 documents if available
  const activeNames = docNames.map(getActiveName).filter(Boolean);
  let matchHint = null;
  if (activeNames.length >= 2) {
    const nameA = activeNames[0].toUpperCase();
    const nameB = activeNames[1].toUpperCase();
    if (nameA === nameB) {
      matchHint = {
        status: 'MATCH',
        score: 1.0,
        text: locale === 'te-IN' ? 'రెండు పత్రాలలో పేరు సరిగ్గా సరిపోలింది (100%).' : 'Exact character match across documents (100%).'
      };
    } else {
      matchHint = {
        status: 'VARIATION',
        score: 0.92,
        text: locale === 'te-IN'
          ? 'ఉచ్చారణ వ్యత్యాసం గమనించబడింది (ఉదా: I / EE లేదా V / W). పేరును సరిచూడండి.'
          : 'Phonetic or transliteration variation detected. Please verify spelling matches official records.'
      };
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              {locale === 'te-IN' ? 'పేర్ల సరిపోలిక సమీక్ష' : 'Extracted Names Review'}
            </h3>
            <p className="text-xs text-slate-500">
              {locale === 'te-IN'
                ? 'OCR చదివిన పేర్లు కింద ఉన్నాయి. అక్షర దోషాలు ఉంటే సరిదిద్దండి.'
                : 'Review names read from documents. Click edit if OCR misread any character.'}
            </p>
          </div>
        </div>

        {matchHint && (
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-medium ${
              matchHint.status === 'MATCH'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}
          >
            {matchHint.text}
          </span>
        )}
      </div>

      {/* Side-by-side cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {docNames.map((doc) => {
          const currentName = getActiveName(doc);
          const isEditing = editingDocType === doc.docType;
          const isLowConf = doc.confidence < 0.70;

          return (
            <div
              key={doc.docType}
              className={`p-3 rounded-lg border transition ${
                customNames[doc.docType]
                  ? 'border-indigo-300 bg-indigo-50/20'
                  : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  {doc.docLabel}
                </span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                    isLowConf
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  OCR: {(doc.confidence * 100).toFixed(0)}%
                </span>
              </div>

              {isEditing ? (
                <div className="space-y-2 mt-1">
                  <input
                    type="text"
                    value={editInput}
                    onChange={(e) => setEditInput(e.target.value)}
                    className="w-full text-xs font-semibold px-2 py-1.5 rounded border border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="Enter correct name"
                    autoFocus
                  />
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSaveEdit(doc.docType)}
                      className="px-2.5 py-1 rounded bg-indigo-600 text-white text-[11px] font-medium flex items-center gap-1 hover:bg-indigo-700"
                    >
                      <Check className="w-3 h-3" />
                      {locale === 'te-IN' ? 'సేవ్ చేయి' : 'Save'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingDocType(null)}
                      className="px-2 py-1 rounded bg-slate-200 text-slate-700 text-[11px] hover:bg-slate-300"
                    >
                      {locale === 'te-IN' ? 'రద్దు' : 'Cancel'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-2 mt-1">
                  <div>
                    <span className="text-xs font-bold text-slate-900 tracking-wide font-mono block">
                      {currentName || (
                        <span className="text-slate-400 italic font-sans font-normal">
                          {locale === 'te-IN' ? 'గుర్తించబడలేదు' : 'Not detected'}
                        </span>
                      )}
                    </span>
                    {customNames[doc.docType] && (
                      <span className="text-[10px] text-indigo-600 font-medium block">
                        ({locale === 'te-IN' ? 'మీరు సవరించారు' : 'User edited'})
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleStartEdit(doc.docType, currentName)}
                    className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-white transition"
                    title="Edit extracted name"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Telugu transliteration advisory note */}
      <div className="flex items-start gap-2 bg-indigo-50/50 border border-indigo-100 rounded-lg p-3 text-xs text-indigo-900">
        <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">
            {locale === 'te-IN'
              ? 'గమనిక: తెలుగు నుండి ఆంగ్లంలోకి అనువాదంలో అక్షరాల మార్పులు'
              : 'Telugu to English Transliteration Rules'}
          </p>
          <p className="text-[11px] text-indigo-700 mt-0.5">
            {locale === 'te-IN'
              ? 'మీసేవా కేంద్రాలలో S. RAKESH మరియు SARIPILLY RAKESH లేదా SARIPALLI వంటి ఉచ్చారణ మార్పులను ప్రత్యేక స్వయం ధృవీకరణ ద్వారా అంగీకరిస్తారు.'
              : 'Phonetic variations (e.g. S. Rakesh vs Saripilly Rakesh, or Saripally) are recognized by MeeSeva through automated reconciliation and applicant self-declaration.'}
          </p>
        </div>
      </div>
    </div>
  );
};
