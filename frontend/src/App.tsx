import React, { useState } from 'react';
import { Header } from './components/Header';
import { CitizenView } from './pages/CitizenView';
import { OperatorDesktop } from './pages/OperatorDesktop';
import { useOnlineStatus } from './hooks/useOnlineStatus';
import { useTranslation } from './hooks/useTranslation';
import { ShieldAlert } from 'lucide-react';

export const App: React.FC = () => {
  const { t } = useTranslation();
  const isOnline = useOnlineStatus();
  const [currentView, setCurrentView] = useState<'citizen' | 'operator'>('citizen');
  const [processingMode, setProcessingMode] = useState<'real' | 'demo'>('demo');
  const [operatorQrToken, setOperatorQrToken] = useState<string>('');

  const handleNavigateToOperator = (qrPayload: string) => {
    setOperatorQrToken(qrPayload);
    setCurrentView('operator');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col selection:bg-brand-500 selection:text-white">
      {/* Global Header */}
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        isOnline={isOnline}
        processingMode={processingMode}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        {currentView === 'citizen' ? (
          <CitizenView
            onNavigateToOperator={handleNavigateToOperator}
            setProcessingMode={setProcessingMode}
          />
        ) : (
          <OperatorDesktop
            initialQrPayload={operatorQrToken}
            onBackToCitizen={() => setCurrentView('citizen')}
          />
        )}
      </main>

      {/* Footer & Mandatory Legal Disclaimer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        <div className="max-w-4xl mx-auto px-4 space-y-2">
          <div className="flex items-center justify-center space-x-1.5 text-slate-700 font-semibold">
            <ShieldAlert className="w-4 h-4 text-brand-600" />
            <span>SevaDristi — Document Pre-Verification Assistant (Telangana MeeSeva & CSC)</span>
          </div>

          <p className="text-[11px] leading-relaxed text-slate-500">
            {t('government_disclaimer')}
          </p>

          <p className="text-[10px] text-slate-400">
            Privacy-by-Design Architecture: In-memory stream processing with zero persistent image disk storage.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
