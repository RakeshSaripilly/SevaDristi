import React, { useState } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { TTSService } from '../services/tts';
import { useTranslation } from '../hooks/useTranslation';

interface AudioAdvisoryPlayerProps {
  textToSpeak: string;
}

export const AudioAdvisoryPlayer: React.FC<AudioAdvisoryPlayerProps> = ({ textToSpeak }) => {
  const { locale, t } = useTranslation();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [hasVoiceError, setHasVoiceError] = useState(false);

  const tts = TTSService.getInstance();

  const handleTogglePlay = () => {
    if (isSpeaking) {
      tts.stop();
      setIsSpeaking(false);
      return;
    }

    setHasVoiceError(false);
    const started = tts.speak(
      textToSpeak,
      locale,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false),
      () => {
        setIsSpeaking(false);
        setHasVoiceError(true);
      }
    );

    if (!started) {
      setHasVoiceError(true);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={handleTogglePlay}
        className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all ${
          isSpeaking
            ? 'bg-amber-600 hover:bg-amber-700 text-white animate-pulse'
            : 'bg-white hover:bg-slate-100 text-slate-800 border border-slate-300'
        }`}
      >
        {isSpeaking ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>{t('stop_audio')}</span>
          </>
        ) : (
          <>
            <Volume2 className="w-3.5 h-3.5 text-brand-600" />
            <span>{t('play_audio_advisory')}</span>
          </>
        )}
      </button>

      {isSpeaking && (
        <span className="text-xs text-amber-700 font-medium flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
          <span>{t('speaking_indicator')}</span>
        </span>
      )}

      {hasVoiceError && (
        <span className="text-xs text-slate-500 flex items-center gap-1">
          <VolumeX className="w-3.5 h-3.5 text-slate-400" />
          <span>{t('tts_unavailable_note')}</span>
        </span>
      )}
    </div>
  );
};
