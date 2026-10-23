import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, AlertTriangle, CheckCircle, RefreshCw, X, Sparkles } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface RealUploaderProps {
  docType: string;
  docLabel: string;
  onFileSelected: (file: File, qualityScore: number, isBlurred: boolean, hasGlare: boolean) => void;
  existingFile?: File | null;
  onRemove?: () => void;
}

export const RealUploader: React.FC<RealUploaderProps> = ({
  docType,
  docLabel,
  onFileSelected,
  existingFile,
  onRemove,
}) => {
  const { locale } = useTranslation();
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [blurScore, setBlurScore] = useState<number | null>(null);
  const [glareRatio, setGlareRatio] = useState<number | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // If existingFile changes, load preview
  useEffect(() => {
    if (existingFile) {
      const url = URL.createObjectURL(existingFile);
      setPreviewUrl(url);
      analyzeClientSideImage(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
      setBlurScore(null);
      setGlareRatio(null);
    }
  }, [existingFile]);

  // Clean up camera stream on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      setIsCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.warn('Camera access denied or unavailable:', err);
      setIsCameraActive(false);
      alert(locale === 'te-IN' 
        ? 'కెమెరా అందుబాటులో లేదు. దయచేసి గ్యాలరీ లేదా ఫైల్ ద్వారా అప్‌లోడ్ చేయండి.' 
        : 'Camera access unavailable. Please select file from gallery/disk.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    stopCamera();

    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `${docType}_capture.jpg`, { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      analyzeClientSideImage(url, file);
    }, 'image/jpeg', 0.90);
  };

  const analyzeClientSideImage = (imgUrl: string, fileObj?: File) => {
    setIsAnalyzing(true);
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      // Scale down to max 400px width for fast Laplacian analysis in JS
      const scale = Math.min(1.0, 400 / img.width);
      const w = Math.floor(img.width * scale);
      const h = Math.floor(img.height * scale);

      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        setIsAnalyzing(false);
        return;
      }

      ctx.drawImage(img, 0, 0, w, h);
      const imgData = ctx.getImageData(0, 0, w, h);
      const data = imgData.data;

      // 1. Grayscale & Glare check
      const gray = new Float32Array(w * h);
      let glareCount = 0;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        // Luminance
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;
        gray[i / 4] = lum;
        // High brightness glare detection
        if (r > 240 && g > 240 && b > 240) {
          glareCount++;
        }
      }
      const glare = glareCount / (w * h);
      setGlareRatio(Number(glare.toFixed(4)));

      // 2. Discrete Laplacian variance
      // Kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
      let sum = 0;
      let sumSq = 0;
      let count = 0;

      for (let y = 1; y < h - 1; y++) {
        for (let x = 1; x < w - 1; x++) {
          const idx = y * w + x;
          const lap =
            gray[idx - w] +
            gray[idx + w] +
            gray[idx - 1] +
            gray[idx + 1] -
            4 * gray[idx];

          sum += lap;
          sumSq += lap * lap;
          count++;
        }
      }

      const mean = sum / count;
      const variance = (sumSq / count) - (mean * mean);
      const calculatedScore = Number(Math.max(0, variance).toFixed(1));
      setBlurScore(calculatedScore);
      setIsAnalyzing(false);

      const isBlur = calculatedScore < 110.0;
      const hasGlareIssue = glare > 0.08;

      if (fileObj) {
        onFileSelected(fileObj, calculatedScore, isBlur, hasGlareIssue);
      }
    };
    img.src = imgUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      analyzeClientSideImage(url, file);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      analyzeClientSideImage(url, file);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-800">{docLabel}</h4>
          <span className="text-xs text-slate-400 uppercase tracking-wider">{docType}</span>
        </div>
        {previewUrl && onRemove && (
          <button
            onClick={onRemove}
            className="p-1 rounded-full text-slate-400 hover:text-red-500 hover:bg-red-50 transition"
            title="Remove document"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Live Camera View */}
      {isCameraActive ? (
        <div className="relative rounded-lg overflow-hidden bg-black aspect-video flex items-center justify-center">
          <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          <div className="absolute inset-0 border-2 border-emerald-400/60 pointer-events-none rounded-lg m-4" />
          <div className="absolute bottom-3 left-0 right-0 flex items-center justify-center gap-3">
            <button
              onClick={capturePhoto}
              className="px-5 py-2 rounded-full bg-emerald-600 text-white font-medium text-xs flex items-center gap-2 shadow-lg hover:bg-emerald-700 transition"
            >
              <Camera className="w-4 h-4" />
              {locale === 'te-IN' ? 'ఫోటో తీయండి' : 'Capture Photo'}
            </button>
            <button
              onClick={stopCamera}
              className="px-3 py-2 rounded-full bg-slate-800/80 text-white text-xs hover:bg-slate-700 transition"
            >
              {locale === 'te-IN' ? 'రద్దు చేయి' : 'Cancel'}
            </button>
          </div>
        </div>
      ) : previewUrl ? (
        /* Image Preview & Quality Badges */
        <div className="space-y-3">
          <div className="relative rounded-lg overflow-hidden border border-slate-200 bg-slate-50 aspect-video flex items-center justify-center group">
            <img src={previewUrl} alt={docLabel} className="max-h-full max-w-full object-contain" />
            <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 bg-white text-slate-800 rounded-md text-xs font-medium shadow hover:bg-slate-100 flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                {locale === 'te-IN' ? 'మళ్ళీ తీయండి' : 'Retake'}
              </button>
            </div>
          </div>

          {/* Real-time Quality Indicators */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {isAnalyzing ? (
              <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 flex items-center gap-1.5 animate-pulse">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                {locale === 'te-IN' ? 'నాణ్యత తనిఖీ జరుగుతోంది...' : 'Analyzing photo quality...'}
              </span>
            ) : (
              <>
                {blurScore !== null && (
                  <span
                    className={`px-2.5 py-1 rounded-full font-medium flex items-center gap-1 ${
                      blurScore >= 110
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}
                  >
                    {blurScore >= 110 ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                    {locale === 'te-IN' ? 'స్పష్టత' : 'Sharpness'}: {blurScore}
                    {blurScore < 110 && (
                      <span className="font-normal opacity-90">
                        ({locale === 'te-IN' ? 'అస్పష్టం, 15 సెం.మీ దగ్గరగా తీయండి' : 'Blurry, retake closer'})
                      </span>
                    )}
                  </span>
                )}

                {glareRatio !== null && glareRatio > 0.08 && (
                  <span className="px-2.5 py-1 rounded-full font-medium bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {locale === 'te-IN' ? 'ఫ్లాష్ వెలుగు ఎక్కువ' : 'High Flash Glare'} ({(glareRatio * 100).toFixed(0)}%)
                  </span>
                )}
              </>
            )}
          </div>
        </div>
      ) : (
        /* Empty Upload Dropzone with Camera / Disk Options */
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-5 text-center transition ${
            isDragOver ? 'border-indigo-500 bg-indigo-50/50' : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
              <Upload className="w-5 h-5 text-slate-600" />
            </div>
            <div className="text-xs text-slate-600">
              <span className="font-semibold text-indigo-600 cursor-pointer hover:underline" onClick={() => fileInputRef.current?.click()}>
                {locale === 'te-IN' ? 'ఫైల్ ఎంచుకోండి' : 'Upload file'}
              </span>{' '}
              {locale === 'te-IN' ? 'లేదా లాగి ఇక్కడ వేయండి' : 'or drag and drop'}
            </div>
            <p className="text-[10px] text-slate-400">JPG, PNG (max 10MB) — Zero disk persistence</p>

            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={startCamera}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-700 text-xs font-medium hover:bg-slate-50 flex items-center gap-1.5 shadow-sm transition"
              >
                <Camera className="w-3.5 h-3.5 text-indigo-600" />
                {locale === 'te-IN' ? 'కెమెరాతో తీయండి' : 'Open Camera'}
              </button>
            </div>
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};
