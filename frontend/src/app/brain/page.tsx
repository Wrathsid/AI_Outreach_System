'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Brain, CheckCircle, RefreshCw, Database, 
  FileText, Lock, Upload, Link, Globe, Mic, 
  Sliders, Save, Check, Loader2, X, Tag
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';

export default function PersonalBrain() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncComplete, setSyncComplete] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [showSkillsModal, setShowSkillsModal] = useState(false);
  const [extractionWarning, setExtractionWarning] = useState<string | null>(null);
  const [verificationMsg, setVerificationMsg] = useState('');
  
  // Restored State
  const [isUploading, setIsUploading] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [useEmoji, setUseEmoji] = useState(false);
  const [formality, setFormality] = useState(75);
  const [length, setLength] = useState(30);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadBrainContext = useCallback(async () => {
    const context = await api.getBrainContext();
    setFormality(context.formality);
    setLength(context.detail_level);
    setUseEmoji(context.use_emojis);
    if (context.resume_url) {
      setUploadedFile(context.resume_url);
    }
    if (context.extracted_skills) {
      setExtractedSkills(context.extracted_skills);
    }
  }, []);

  useEffect(() => {
    const fetchContext = async () => {
      try {
        const context = await api.getBrainContext();
        setFormality(context.formality);
        setLength(context.detail_level);
        setUseEmoji(context.use_emojis);
        if (context.resume_url) setUploadedFile(context.resume_url);
        if (context.extracted_skills) setExtractedSkills(context.extracted_skills);
      } catch (e) {
        console.error("Failed to load brain context", e);
      }
    };
    fetchContext();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncComplete(false);
    await new Promise(resolve => setTimeout(resolve, 2000));
    await loadBrainContext();
    setIsSyncing(false);
    setSyncComplete(true);
    setTimeout(() => setSyncComplete(false), 3000);
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    await api.updateBrainContext(formality, length, useEmoji);
    setIsSaving(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    // Reset state before upload
    setUploadedFile(null);
    setExtractedSkills([]);
    
    const result = await api.uploadResume(file);
    if (result) {
      setUploadedFile(result.filename);
      // Always update skills, defaulting to empty array if null
      setExtractedSkills(result.extracted_skills || []);
      setExtractionWarning(result.warning || null);
    }
    setIsUploading(false);
  };

  const handleVerify = async () => {
    if (!linkedinUrl) return;
    setIsVerifying(true);
    setVerificationMsg('');
    
    const result = await api.verifyLinkedIn(linkedinUrl);
    
    if (result.valid) {
      setIsVerified(true);
      setVerificationMsg('');
    } else {
      setIsVerified(false);
      setVerificationMsg(result.message);
    }
    setIsVerifying(false);
  };
  
  /* Save function was removed as it's not needed for Brain Context anymore (auto-saves on upload) */
  /* Brain training percent calculation */
  const trainingPercent = uploadedFile ? (isVerified ? 85 : 75) : (isVerified ? 70 : 65);

  return (
    <div className="flex-1 h-full overflow-y-auto relative scroll-smooth bg-background-dark/50">
      <div className="fixed inset-0 bg-[#0F0F12] -z-20"></div>
      <div className="fixed inset-0 opacity-15 pointer-events-none -z-10" style={{ backgroundImage: 'radial-gradient(at 0% 0%, hsla(240, 80%, 15%, 0.3) 0, transparent 50%), radial-gradient(at 100% 100%, hsla(240, 80%, 10%, 0.3) 0, transparent 50%)' }}></div>

      <div className="max-w-5xl mx-auto px-6 py-10 lg:px-12 lg:py-14 flex flex-col gap-10">
        
        {/* Page Header */}
        <header className="flex flex-col gap-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex flex-col gap-2 max-w-2xl">
              <h1 className="text-4xl font-bold text-white tracking-tight">Train Your Personal Brain</h1>
              <p className="text-gray-400 text-lg font-light leading-relaxed">Upload your professional DNA. This helps your assistant represent you accurately in every interaction.</p>
            </div>
            <button 
              onClick={handleSync}
              disabled={isSyncing}
              className="flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-blue-600 text-white rounded-lg shadow-[0_0_20px_rgba(25,25,230,0.3)] transition-all transform hover:scale-105 active:scale-95 font-medium text-sm disabled:opacity-70"
            >
              {isSyncing ? (
                <Loader2 size={20} className="animate-spin" />
              ) : syncComplete ? (
                <Check size={20} />
              ) : (
                <RefreshCw size={20} />
              )}
              {syncComplete ? 'Synced!' : 'Sync Context'}
            </button>
          </div>

          {/* Progress Bar */}
          <div className="glass-panel p-6 rounded-xl flex flex-col gap-3 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Brain size={64} className="text-primary" />
            </div>
            <div className="flex justify-between items-end">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-gray-300">Brain Training Status</span>
                <span className="text-xs text-primary mt-1 flex items-center gap-1">
                  <CheckCircle size={14} />
                  {trainingPercent >= 80 ? 'Great context level' : trainingPercent >= 70 ? 'Good context level' : 'Add more data'}
                </span>
              </div>
              <span className="text-2xl font-bold text-white">{trainingPercent}%</span>
            </div>
            <div className="h-2 w-full bg-gray-700/50 rounded-full overflow-hidden mt-1">
              <div className="h-full bg-primary rounded-full shadow-[0_0_10px_rgba(25,25,230,0.5)] transition-all duration-500" style={{ width: `${trainingPercent}%` }}></div>
            </div>
          </div>
        </header>

        {/* Hard Data Sources */}
        <section className="flex flex-col gap-5">
          <div className="flex items-center gap-2 px-1">
            <Database className="text-gray-400" size={24} />
            <h2 className="text-xl font-semibold text-white tracking-tight">Hard Data Sources</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Resume Upload */}
            <div className="glass-panel rounded-2xl p-6 flex flex-col gap-4 relative overflow-hidden">
               <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/5 rounded-lg text-white">
                    <FileText size={24} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Resume / CV</h3>
                    <p className="text-xs text-gray-400">PDF or DOCX</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowSkillsModal(true)}
                    disabled={extractedSkills.length === 0}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-emerald-400 border border-emerald-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Skills ({extractedSkills.length})
                  </button>
                  <div className="group/tooltip relative">
                    <Lock size={18} className="text-gray-600" />
                    <span className="absolute right-0 -top-8 w-max px-2 py-1 bg-black text-xs text-white rounded opacity-0 group-hover/tooltip:opacity-100 transition-opacity">Private & Encrypted</span>
                  </div>
                </div>
              </div>
               
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf,.docx,.doc,.txt"
                className="hidden"
                onChange={handleFileUpload}
              />
              
              <div 
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed ${uploadedFile ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-gray-700 hover:border-primary/50 hover:bg-primary/5'} transition-all rounded-xl p-8 flex flex-col items-center justify-center gap-3 text-center cursor-pointer group/drop relative overflow-hidden`}
              >
                {isUploading ? (
                  <Loader2 size={24} className="text-primary animate-spin" />
                ) : uploadedFile ? (
                  <>
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center relative z-10">
                      <Check className="text-emerald-400" size={24} />
                    </div>
                    <div className="flex flex-col gap-1 relative z-10">
                      <p className="text-sm font-medium text-emerald-400">{uploadedFile}</p>
                      <p className="text-xs text-gray-500">Click to replace</p>
                      

                    </div>
                    
                    {/* Background Glow */}
                    <div className="absolute inset-0 bg-emerald-500/5 blur-2xl rounded-full transform scale-150 opacity-20 animate-pulse"></div>
                  </>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center group-hover/drop:scale-110 transition-transform duration-300">
                      <Upload className="text-gray-400 group-hover/drop:text-primary" size={24} />
                    </div>
                    <div className="flex flex-col gap-1">
                      <p className="text-sm font-medium text-white">Click to upload or drag and drop</p>
                      <p className="text-xs text-gray-500">Max file size 10MB</p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* LinkedIn URL */}
            <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 justify-between">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/5 rounded-lg text-white">
                    <Link size={24} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">Portfolio / LinkedIn</h3>
                    <p className="text-xs text-gray-400">External validation</p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Primary URL</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Globe size={18} className="text-gray-500" />
                      </div>
                      <input 
                        className={`block w-full pl-10 pr-3 py-2.5 bg-[#111118] border ${verificationMsg ? 'border-red-500/50' : 'border-gray-700'} rounded-lg text-white text-sm placeholder-gray-600 focus:ring-1 focus:ring-primary focus:border-primary transition-colors`} 
                        placeholder="linkedin.com/in/username" 
                        type="text"
                        value={linkedinUrl}
                        onChange={(e) => {
                          setLinkedinUrl(e.target.value);
                          setIsVerified(false);
                          setVerificationMsg('');
                        }}
                      />
                    </div>
                    <button 
                      onClick={handleVerify}
                      disabled={isVerifying || !linkedinUrl}
                      className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
                    >
                      {isVerifying ? <Loader2 size={16} className="animate-spin" /> : 'Verify'}
                    </button>
                  </div>
                  {verificationMsg && (
                    <p className="text-xs text-red-400 mt-1">{verificationMsg}</p>
                  )}
                </div>
                {isVerified && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg w-fit">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs text-green-400 font-medium">Verified Valid Profile</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-5 pb-10">
          <div className="flex items-center gap-2 px-1">
            <Mic className="text-gray-400" size={24} />
            <h2 className="text-xl font-semibold text-white tracking-tight">Voice Settings</h2>
          </div>
          
          <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/5 rounded-lg text-white">
                  <Sliders size={24} />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">AI Tone Configuration</h3>
                  <p className="text-xs text-gray-400">How AI speaks for you</p>
                </div>
              </div>
              <button 
                onClick={handleSaveSettings}
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-all"
              >
                {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Save
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Formality */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between text-xs font-medium text-gray-400">
                  <span>Casual</span>
                  <span>Formal</span>
                </div>
                <input 
                  className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                  max="100" 
                  min="0" 
                  type="range" 
                  value={formality}
                  onChange={(e) => setFormality(Number(e.target.value))}
                />
                <p className="text-center text-xs text-slate-500">Formality: {formality}%</p>
              </div>
              
              {/* Length */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between text-xs font-medium text-gray-400">
                  <span>Concise</span>
                  <span>Detailed</span>
                </div>
                <input 
                  className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                  max="100" 
                  min="0" 
                  type="range" 
                  value={length}
                  onChange={(e) => setLength(Number(e.target.value))}
                />
                <p className="text-center text-xs text-slate-500">Detail: {length}%</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Floating Save for Mobile */}
      <button onClick={handleSaveSettings} className="lg:hidden fixed bottom-6 right-6 w-14 h-14 bg-primary text-white rounded-full shadow-lg flex items-center justify-center z-50">
        <Save size={24} />
      </button>

      {/* Skills Modal */}
      <AnimatePresence>
        {showSkillsModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowSkillsModal(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative bg-[#1A1A24] border border-white/10 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
            >
              <div className="p-6 border-b border-white/10 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                    <Tag size={20} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Extracted Skills</h3>
                    <p className="text-sm text-gray-400">Detected from your resume</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowSkillsModal(false)}
                  className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="p-6 max-h-[60vh] overflow-y-auto">
                {extractedSkills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {extractedSkills.map((skill, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="flex items-center gap-2 px-3 py-2 bg-emerald-500/5 hover:bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-sm font-medium transition-colors"
                      >
                         <Tag size={12} />
                         {skill}
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-10 text-gray-500 flex flex-col items-center gap-2">
                    <p>No skills detected yet.</p>
                    {extractionWarning && (
                      <div className="mt-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg max-w-xs">
                        <p className="text-xs text-yellow-400 text-center">
                           ⚠️ {extractionWarning}
                        </p>
                      </div>
                    )}
                    {!extractionWarning && (
                      <p className="text-sm mt-1 max-w-xs text-center">
                         If you just uploaded, ensure your resume contains text and is not an image.
                      </p>
                    )}
                  </div>
                )}
              </div>
              
              <div className="p-4 bg-white/5 border-t border-white/10 text-center">
                 <button 
                   onClick={() => setShowSkillsModal(false)}
                   className="text-sm text-gray-400 hover:text-white transition-colors"
                 >
                   Close
                 </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
