import { Sparkles, Camera, ShieldCheck, ArrowRight, X } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ isOpen, onClose }) => {
  const { locale } = useTranslation();

  if (!isOpen) return null;

  const steps = [
    {
      num: 1,
      icon: <Sparkles className="w-5 h-5 text-indigo-600" />,
      title_en: '1. Select Welfare Scheme',
      title_te: '1. సంక్షేమ పథకాన్ని ఎంచుకోండి',
      desc_en: 'Choose ePASS Scholarship, Aasara Pension, or Rythu Bharosa to view specific requirements.',
      desc_te: 'మీకు అవసరమైన ePASS, ఆసరా పెన్షన్ లేదా రైతు భరోసా పథకాన్ని ఎంచుకోండి.'
    },
    {
      num: 2,
      icon: <Camera className="w-5 h-5 text-indigo-600" />,
      title_en: '2. Capture Clear Photos',
      title_te: '2. స్పష్టమైన ఫోటోలు తీయండి',
      desc_en: 'Hold phone 15cm away under bright light. Our instant quality gate checks blur and flash glare in real time.',
      desc_te: '15 సెం.మీ దూరంలో మంచి వెలుతురులో ఫోటో తీయండి. బ్లర్ మరియు ఫ్లాష్ వెలుగును తక్షణమే తనిఖీ చేస్తుంది.'
    },
    {
      num: 3,
      icon: <ShieldCheck className="w-5 h-5 text-indigo-600" />,
      title_en: '3. Download PDF & QR Token',
      title_te: '3. PDF మరియు QR టోకెన్ పొందండి',
      desc_en: 'Review extracted names, correct any typos, and take the cryptographically signed QR to MeeSeva for fast processing.',
      desc_te: 'పేర్లను సరిచూసి, సంతకం చేసిన QR టోకెన్‌తో మీసేవా కేంద్రానికి వెళ్ళి సులభంగా దరఖాస్తు చేయండి.'
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Sparkles className="w-5 h-5" />
            </span>
            <h3 className="text-base font-bold text-slate-900">
              {locale === 'te-IN' ? 'సేవాదృష్టి ఎలా పనిచేస్తుంది?' : 'How SevaDristi Works'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4">
          {steps.map((step) => (
            <div key={step.num} className="flex items-start gap-3.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="p-2 bg-white rounded-lg shadow-sm border border-slate-200 shrink-0">
                {step.icon}
              </div>
              <div className="text-left space-y-0.5">
                <h4 className="text-xs font-bold text-slate-800">
                  {locale === 'te-IN' ? step.title_te : step.title_en}
                </h4>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {locale === 'te-IN' ? step.desc_te : step.desc_en}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="pt-2">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md flex items-center justify-center gap-2 transition"
          >
            <span>{locale === 'te-IN' ? 'మొదలు పెట్టండి' : 'Get Started'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
