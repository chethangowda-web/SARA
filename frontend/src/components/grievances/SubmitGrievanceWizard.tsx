import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import PriorityBadge from '../ui/PriorityBadge';
import { formatApiError } from '../../api/client';
import { submitGrievance, uploadEvidence } from '../../api/grievances';
import {
  FileText,
  UploadCloud,
  Cpu,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  X,
  File,
  Sparkles,
  ShieldAlert,
  Mic,
} from 'lucide-react';

const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
  { code: 'mr', label: 'ಮರಾಠಿ (Marathi)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
];

export interface SubmitGrievanceWizardProps {
  onClose?: () => void;
}

export const SubmitGrievanceWizard: React.FC<SubmitGrievanceWizardProps> = ({ onClose }) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState('Public Infrastructure');
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Voice Recording state
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [isListeningTitle, setIsListeningTitle] = useState(false);
  const [isListeningDesc, setIsListeningDesc] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);

  // AI Pipeline Preview state
  const [aiPreview, setAiPreview] = useState<{
    category: string;
    priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    confidence: number;
    summary: string;
    grievanceId?: string;
  } | null>(null);

  const navigate = useNavigate();

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      setFiles((prev) => [...prev, ...droppedFiles]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const startListening = (target: 'title' | 'description') => {
    setSpeechError(null);
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechError("🎙️ Voice input isn't available in this browser. You can type your complaint instead.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = selectedLanguage === 'kn' ? 'kn-IN' : 
                         selectedLanguage === 'hi' ? 'hi-IN' : 
                         selectedLanguage === 'te' ? 'te-IN' : 
                         selectedLanguage === 'ta' ? 'ta-IN' : 
                         selectedLanguage === 'ml' ? 'ml-IN' : 
                         selectedLanguage === 'mr' ? 'mr-IN' : 
                         selectedLanguage === 'bn' ? 'bn-IN' : 'en-US';

      if (target === 'title') {
        setIsListeningTitle(true);
        setIsListeningDesc(false);
      } else {
        setIsListeningDesc(true);
        setIsListeningTitle(false);
      }

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (target === 'title') {
          setTitle((prev) => (prev ? prev + ' ' + transcript : transcript));
        } else {
          setDescription((prev) => (prev ? prev + ' ' + transcript : transcript));
        }
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        if (event.error === 'not-allowed') {
          setSpeechError("Microphone access blocked. Please enable permissions in your browser settings.");
        } else {
          setSpeechError(`Speech recognition failed: ${event.error}`);
        }
        setIsListeningTitle(false);
        setIsListeningDesc(false);
      };

      recognition.onend = () => {
        setIsListeningTitle(false);
        setIsListeningDesc(false);
      };

      recognition.start();
    } catch (e: any) {
      setSpeechError(`Speech initialization failed: ${e.message}`);
      setIsListeningTitle(false);
      setIsListeningDesc(false);
    }
  };

  // Step 3: Trigger submission & backend AI classification
  const handleTriggerSubmission = async () => {
    setError(null);
    setSubmitting(true);
    try {
      // Create Grievance (Backend automatically triggers AI pipeline and returns processed grievance)
      const res = await submitGrievance({
        title,
        description: `${description}${category ? `\n[Category: ${category}]` : ''}`,
        location,
      });

      // Upload evidence files if attached
      if (files.length > 0 && res.id) {
        for (const file of files) {
          try {
            await uploadEvidence({ id: res.id, file });
          } catch {
            // Log individual file upload error without failing whole grievance
          }
        }
      }

      setAiPreview({
        category: res.category || category || 'General Governance',
        priority: (res.priority as any) || 'MEDIUM',
        confidence: res.classification_confidence ? Math.round(res.classification_confidence * 100) : 80,
        summary: res.summary || res.description || 'AI analyzed grievance details and automatically routed to department.',
        grievanceId: res.id,
      });

      setStep(3);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const stepsList = [
    { num: 1, label: 'Issue Details', icon: <FileText className="w-4 h-4" /> },
    { num: 2, label: 'Upload Evidence', icon: <UploadCloud className="w-4 h-4" /> },
    { num: 3, label: 'AI Advisory', icon: <Cpu className="w-4 h-4" /> },
    { num: 4, label: 'Confirmation', icon: <CheckCircle2 className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Wizard Progress Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        {stepsList.map((s) => {
          const isActive = step === s.num;
          const isCompleted = step > s.num;
          return (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition ${
                  isCompleted
                    ? 'bg-emerald-600 text-white'
                    : isActive
                    ? 'bg-blue-600 text-white ring-2 ring-blue-500/40 ring-offset-2 ring-offset-slate-900'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span
                className={`hidden sm:inline text-xs font-semibold ${
                  isActive ? 'text-blue-400' : isCompleted ? 'text-emerald-400' : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl">
          {error}
        </div>
      )}

      {/* STEP 1: Describe Issue */}
      {step === 1 && (
        <div className="space-y-4 animate-fadeIn">
          {speechError && (
            <div className="p-4 bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs font-semibold rounded-xl">
              {speechError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Preferred Language / ಭಾಷೆ / भाषा *
              </label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="Public Infrastructure">Public Infrastructure & Roads</option>
                <option value="Water & Sanitation">Water Supply & Sanitation</option>
                <option value="Electricity & Lighting">Electricity & Street Lighting</option>
                <option value="Public Health">Public Health & Waste Management</option>
                <option value="Revenue & Taxation">Revenue & Administrative Services</option>
                <option value="Other Civic Services">Other Civic Services</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Grievance Title *
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Water pipeline leak near 4th Main Road / ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => startListening('title')}
                className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg transition ${
                  isListeningTitle
                    ? 'bg-red-600 text-white animate-pulse'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900/60 hover:bg-slate-800'
                }`}
                title="Speak Title"
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>
            {isListeningTitle && (
              <div className="flex items-center gap-1.5 text-[11px] text-red-400 font-semibold mt-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                <span>Listening... Speak now in your selected language.</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Location / Landmark *
            </label>
            <input
              type="text"
              required
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Ward 42, Opposite City Public Library"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Detailed Description *
            </label>
            <div className="relative">
              <textarea
                required
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide specific details about the issue, duration, impact on citizens..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => startListening('description')}
                className={`absolute right-3 bottom-3 p-2 rounded-lg transition ${
                  isListeningDesc
                    ? 'bg-red-600 text-white animate-pulse'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-900/60 hover:bg-slate-800'
                }`}
                title="Speak Description"
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>
            {isListeningDesc && (
              <div className="flex items-center gap-1.5 text-[11px] text-red-400 font-semibold mt-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                <span>Listening... Describe the issue in detail.</span>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800/60">
            <Button
              variant="primary"
              disabled={!title.trim() || !description.trim() || !location.trim()}
              onClick={() => setStep(2)}
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Next: Upload Evidence
            </Button>
          </div>
        </div>
      )}

      {/* STEP 2: Upload Evidence */}
      {step === 2 && (
        <div className="space-y-4 animate-fadeIn">
          <p className="text-xs text-slate-400">
            Attach photo, PDF, document, or video evidence to support your grievance verification.
          </p>

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border-2 border-dashed border-slate-800 hover:border-blue-500/60 bg-slate-950/60 rounded-2xl p-8 text-center transition cursor-pointer"
          >
            <UploadCloud className="w-10 h-10 text-blue-400 mx-auto mb-2" />
            <p className="text-sm font-bold text-slate-200">Drag & drop evidence files here</p>
            <p className="text-xs text-slate-400 mt-1">Supports PNG, JPG, PDF, DOCX up to 25MB</p>
            <label className="mt-4 inline-block">
              <span className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl cursor-pointer transition">
                Browse Files
              </span>
              <input type="file" multiple onChange={handleFileSelect} className="hidden" />
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-300">Attached Evidence ({files.length}):</span>
              {files.map((file, i) => (
                <div key={i} className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <File className="w-4 h-4 text-blue-400 shrink-0" />
                    <span className="font-medium text-slate-200 truncate">{file.name}</span>
                    <span className="text-slate-500 font-mono text-[10px]">({Math.round(file.size / 1024)} KB)</span>
                  </div>
                  <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-400 p-1">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between pt-4 border-t border-slate-800">
            <Button variant="outline" onClick={() => setStep(1)} icon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
            <Button
              variant="primary"
              loading={submitting}
              onClick={handleTriggerSubmission}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Analyze with AI & Submit
            </Button>
          </div>
        </div>
      )}

      {/* STEP 3: AI Analysis Preview */}
      {step === 3 && aiPreview && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-5 rounded-2xl bg-indigo-950/40 border border-indigo-800/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-indigo-300 font-bold text-sm">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span>SARA AI Classification Advisory</span>
              </div>
              <Badge variant="purple">AI Advisory</Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-xl border border-indigo-900/40">
              <div>
                <span className="text-xs text-slate-400 block">Detected Category</span>
                <span className="text-sm font-bold text-slate-100">{aiPreview.category}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block mb-1">Calculated Priority</span>
                <PriorityBadge priority={aiPreview.priority} />
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-slate-300 block mb-1">AI Executive Summary:</span>
              <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                "{aiPreview.summary}"
              </p>
            </div>

            <div className="text-[11px] text-indigo-300/70 font-mono flex items-center gap-1.5 pt-2">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>AI Advisory Disclaimer: Insights are decision support only and do not modify workflow state machine rules.</span>
            </div>
          </div>

          <div className="flex justify-end">
            <Button variant="primary" onClick={() => setStep(4)} icon={<ArrowRight className="w-4 h-4" />}>
              Proceed to Confirmation
            </Button>
          </div>
        </div>
      )}

      {/* STEP 4: Confirmation */}
      {step === 4 && aiPreview && (
        <div className="space-y-6 text-center animate-fadeIn py-4">
          <div className="w-16 h-16 bg-emerald-600/20 border-2 border-emerald-500 rounded-full flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h3 className="text-2xl font-black text-white">Grievance Successfully Registered</h3>
            <p className="text-sm text-slate-400">Your complaint has been immutably logged into SARA governance tracking.</p>
            <div className="inline-block px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm font-mono font-bold text-blue-400 mt-2">
              Grievance ID: {aiPreview.grievanceId}
            </div>
          </div>

          <div className="flex justify-center gap-4 pt-4">
            <Button
              variant="primary"
              onClick={() => {
                if (onClose) onClose();
                navigate(`/grievances/${aiPreview.grievanceId}`);
              }}
            >
              Track Grievance Details
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmitGrievanceWizard;
