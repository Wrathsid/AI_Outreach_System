'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  RefreshCw, FileText, Globe, Upload, Link, CheckCircle, Sliders, Loader2, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';

export default function PersonalBrain() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [showSkillsModal, setShowSkillsModal] = useState(false);

  const [verificationMsg, setVerificationMsg] = useState('');
  
  // Restored State
  const [isUploading, setIsUploading] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadBrainContext = useCallback(async () => {
    const context = await api.getBrainContext();
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
    await new Promise(resolve => setTimeout(resolve, 2000));
    await loadBrainContext();
    setIsSyncing(false);
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
    <div className="flex-1 h-full overflow-y-auto bg-[#0F0F12] relative">
      <div className="max-w-3xl mx-auto px-6 py-12 flex flex-col gap-8">
        
        {/* Minimal Header with Consolidated Progress */}
        <header className="flex items-center justify-between">
          <div>
             <h1 className="text-3xl font-bold text-white mb-1">Personal Brain</h1>
             <p className="text-slate-500 text-sm">Train your assistant with your data.</p>
          </div>

          <div className="flex items-center gap-6">
             {/* Progress */}
             <div className="text-right">
                <div className="flex items-center justify-end gap-2 text-primary">
                   <span className="text-3xl font-bold">{trainingPercent}%</span>
                </div>
                <span className="text-xs text-slate-500 font-medium">Training Completeness</span>
             </div>

            <button 
              onClick={handleSync}
              disabled={isSyncing}
              className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              title="Sync Context"
            >
              <RefreshCw size={18} className={isSyncing ? "animate-spin" : ""} />
            </button>
          </div>
        </header>

        {/* Checklist Container */}
        <div className="flex flex-col gap-4">
            
            {/* Item 1: Resume */}
            <div className={`glass-panel border ${uploadedFile ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-white/5'} rounded-2xl overflow-hidden transition-all`}>
                <div className="p-6 flex items-center justify-between cursor-default">
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${uploadedFile ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400'}`}>
                            <FileText size={20} />
                        </div>
                        <div>
                            <h3 className="text-white font-medium text-lg">Resume Context</h3>
                            <p className="text-sm text-slate-500">
                                {uploadedFile ? 'Resume active' : 'Upload PDF/DOCX to train skills'}
                            </p>
                        </div>
                    </div>
                    {uploadedFile ? (
                        <div className="flex items-center gap-3">
                             <button
                                onClick={() => setShowSkillsModal(true)}
                                className="px-3 py-1.5 text-xs font-medium bg-emerald-500/10 text-emerald-400 rounded-lg hover:bg-emerald-500/20 transition-colors"
                             >
                                {extractedSkills.length} Skills Found
                             </button>
                             <CheckCircle className="text-emerald-500" size={24} />
                        </div>
                    ) : (
                        <div className="w-6 h-6 rounded-full border-2 border-slate-700"></div>
                    )}
                </div>

                {/* Expanded Content (Always visible for now if not uploaded, or simple toggle?) 
                    User said "Checklist format... expands on click". 
                    For simplicity, I'll keep the upload area visible if not uploaded, 
                    or small "Replace" button if uploaded.
                */}
                <div className="px-6 pb-6 pl-20">
                      <input 
                        ref={fileInputRef}
                        type="file" 
                        accept=".pdf,.docx,.doc,.txt"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                      
                      {!uploadedFile ? (
                          <div 
                            onClick={() => fileInputRef.current?.click()}
                            className="border border-dashed border-slate-700 hover:border-slate-500 rounded-xl p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors text-center"
                          >
                             {isUploading ? (
                                <Loader2 className="animate-spin text-slate-400" />
                             ) : (
                                <>
                                    <Upload className="text-slate-500 mb-1" size={20} />
                                    <span className="text-sm text-slate-400">Click to upload resume</span>
                                </>
                             )}
                          </div>
                      ) : (
                          <button 
                            onClick={() => fileInputRef.current?.click()}
                            className="text-xs text-slate-500 hover:text-slate-300 underline underline-offset-4"
                          >
                            Replace current resume
                          </button>
                      )}
                </div>
            </div>

            {/* Item 2: LinkedIn */}
            <div className={`glass-panel border ${isVerified ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-white/5'} rounded-2xl overflow-hidden transition-all`}>
                <div className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isVerified ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400'}`}>
                            <Globe size={20} />
                        </div>
                        <div>
                            <h3 className="text-white font-medium text-lg">LinkedIn Validation</h3>
                            <p className="text-sm text-slate-500">
                                {isVerified ? 'Profile verified' : 'Connect profile for accurate outreach'}
                            </p>
                        </div>
                    </div>
                    {isVerified ? (
                        <CheckCircle className="text-emerald-500" size={24} />
                    ) : (
                        <div className="w-6 h-6 rounded-full border-2 border-slate-700"></div>
                    )}
                </div>

                {/* Content */}
                <div className="px-6 pb-6 pl-20">
                    <div className="flex gap-2 max-w-md">
                        <div className="relative flex-1">
                            <input 
                            className={`block w-full px-4 py-2.5 bg-[#1A1A24] border ${verificationMsg ? 'border-red-500/50' : 'border-white/10'} rounded-xl text-white text-sm placeholder-slate-600 focus:outline-none focus:border-primary/50 transition-colors`} 
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
                            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm font-medium text-white transition-colors disabled:opacity-50"
                        >
                            {isVerifying ? <Loader2 size={16} className="animate-spin" /> : 'Verify'}
                        </button>
                    </div>
                    {verificationMsg && (
                    <p className="text-xs text-red-400 mt-2">{verificationMsg}</p>
                    )}
                </div>
            </div>

            {/* Note about Voice Settings */}
            <div className="mt-4 p-4 rounded-xl border border-white/5 bg-white/5 flex items-center gap-3">
                <Sliders size={18} className="text-slate-400" />
                <p className="text-sm text-slate-400">
                    Voice & Tone settings have been moved to the <Link href="/settings" className="text-primary hover:underline">Settings</Link> page.
                </p>
            </div>

        </div>

      </div>

      {/* Floating Save removed, Skills Modal retained */}
      <AnimatePresence>
        {showSkillsModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
             {/* ... Skills Modal Content ... */}
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
               {/* Modal Header */}
               <div className="p-6 border-b border-white/10 flex justify-between items-center">
                   <h3 className="text-lg font-bold text-white">Extracted Skills</h3>
                   <button onClick={() => setShowSkillsModal(false)}><X size={20} className="text-slate-400" /></button>
               </div>
               
               {/* Modal Body */}
               <div className="p-6 max-h-[60vh] overflow-y-auto">
                    <div className="flex flex-wrap gap-2">
                    {extractedSkills.map((skill, i) => (
                        <div key={i} className="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg text-sm border border-emerald-500/20">
                            {skill}
                        </div>
                    ))}
                    {extractedSkills.length === 0 && <p className="text-slate-500 text-sm">No skills found yet.</p>}
                    </div>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
