export class TTSService {
  private static instance: TTSService;
  private voices: SpeechSynthesisVoice[] = [];
  private isLoaded = false;

  private constructor() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.loadVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        this.loadVoices();
      };
    }
  }

  public static getInstance(): TTSService {
    if (!TTSService.instance) {
      TTSService.instance = new TTSService();
    }
    return TTSService.instance;
  }

  private loadVoices() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.voices = window.speechSynthesis.getVoices();
      if (this.voices.length > 0) {
        this.isLoaded = true;
      }
    }
  }

  public getAvailableVoice(locale: string): SpeechSynthesisVoice | null {
    if (!this.isLoaded) {
      this.loadVoices();
    }
    const langCode = locale.split('-')[0].toLowerCase(); // 'te', 'hi', 'en', 'ta'
    // 1. Exact match (e.g. te-IN)
    let match = this.voices.find(v => v.lang.toLowerCase() === locale.toLowerCase());
    if (match) return match;

    // 2. Prefix match (e.g. te)
    match = this.voices.find(v => v.lang.toLowerCase().startsWith(langCode));
    if (match) return match;

    // 3. Fallback to Indian English or English if regional not installed
    match = this.voices.find(v => v.lang.toLowerCase().includes('en-in') || v.lang.toLowerCase().startsWith('en'));
    return match || null;
  }

  public speak(
    text: string,
    locale: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: () => void
  ): boolean {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      if (onError) onError();
      return false;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const voice = this.getAvailableVoice(locale);
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    } else {
      utterance.lang = locale;
    }

    utterance.rate = 0.95; // Slightly slower for clarity
    utterance.pitch = 1.0;

    if (onStart) utterance.onstart = onStart;
    if (onEnd) utterance.onend = onEnd;
    if (onError) utterance.onerror = onError;

    window.speechSynthesis.speak(utterance);
    return true;
  }

  public stop() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
}
