'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  RefreshCw, FileText, Globe, Upload, CheckCircle, Loader2, X, Cpu, Network, Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import NeuralBackground from '@/components/NeuralBackground';

export default function PersonalBrain() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [showSkillsModal, setShowSkillsModal] = useState(false);
  const [verificationMsg, setVerificationMsg] = useState('');
  
  const [isUploading, setIsUploading] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* Scope Fix: loadBrainContext needs to be accessible by handleSync */
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
    loadBrainContext();
  }, [loadBrainContext]);

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
    setUploadedFile(null);
    setExtractedSkills([]);
    
    const result = await api.uploadResume(file);
    if (result) {
      setUploadedFile(result.filename);
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
  
  const trainingPercent = uploadedFile ? (isVerified ? 85 : 75) : (isVerified ? 70 : 65);
  const circumference = 2 * Math.PI * 24; 
  const dashPercentage = (trainingPercent / 100) * circumference;

  return (
    <div className="flex-1 h-full overflow-hidden relative bg-black text-white font-sans selection:bg-cyan-500/30">
      <NeuralBackground />
      
      <div className="relative z-10 h-full flex flex-col p-6 md:p-12 max-w-5xl mx-auto w-full">
        
        {/* Header Section */}
        <header className="flex items-end justify-between mb-12 animate-fade-in-up">
          <div>
             <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                    <Cpu size={24} className="text-cyan-400" />
                </div>
                <h1 className="text-4xl font-bold tracking-tight text-white">
                  The Cortex
                </h1>
             </div>
             <p className="text-slate-400 text-sm font-light max-w-md leading-relaxed">
               Neural interface for assistant training. Upload data to expand semantic understanding and outreach capabilities.
             </p>
          </div>

          <div className="flex items-center gap-8">
             {/* Circular Progress */}
             <div className="relative w-16 h-16 flex items-center justify-center group cursor-default">
                <svg className="w-full h-full transform -rotate-90">
                    <circle cx="32" cy="32" r="24" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-white/5" />
                    <circle 
                        cx="32" cy="32" r="24" 
                        stroke="currentColor" strokeWidth="4" 
                        fill="transparent" 
                        className="text-cyan-500 transition-all duration-1000 ease-out"
                        strokeDasharray={circumference}
                        strokeDashoffset={circumference - dashPercentage}
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className="text-xs font-bold text-white">{trainingPercent}%</span>
                </div>
                
                {/* Tooltip */}
                <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/80 border border-white/10 rounded text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    Synapse Density
                </div>
             </div>

            <button 
              onClick={handleSync}
              disabled={isSyncing}
              className="w-10 h-10 rounded-full bg-white/5 hover:bg-cyan-500/20 border border-white/10 hover:border-cyan-500/50 flex items-center justify-center text-slate-400 hover:text-cyan-400 transition-all duration-300"
              title="Resynchronize Neural Net"
            >
              <RefreshCw size={18} className={isSyncing ? "animate-spin" : ""} />
            </button>
          </div>
        </header>


        {/* Main Grid */}
        <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
            
            <h2 className="text-xs font-mono text-cyan-500/70 uppercase tracking-widest flex items-center gap-2 mb-2">
                <Network size={12} /> Data Ingestion
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Card 1: Resume */}
                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className={`
                        relative group overflow-hidden rounded-2xl p-1 transition-all duration-500
                        ${uploadedFile 
                            ? 'bg-gradient-to-br from-emerald-500/20 via-emerald-500/5 to-transparent border-emerald-500/30 shadow-[0_0_30px_-10px_rgba(16,185,129,0.3)]' 
                            : 'bg-white/5 border border-white/10 hover:border-cyan-500/30'
                        }
                    `}
                >
                    <div className="absolute inset-0 bg-[url('/noise.png')] opacity-10 mix-blend-overlay"></div>
                    <div className="relative bg-[#0a0a0f]/90 backdrop-blur-xl rounded-xl p-6 h-full border border-white/5 flex flex-col">
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${uploadedFile ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-slate-400'}`}>
                                <FileText size={24} />
                            </div>
                            {uploadedFile && <CheckCircle size={20} className="text-emerald-500" />}
                        </div>
                        
                        <h3 className="text-lg font-semibold text-white mb-1">Resume Data</h3>
                        <p className="text-sm text-slate-500 mb-6 font-light flex-1">
                            {uploadedFile ? 'Vectorized and indexed.' : 'Upload CV for skill extraction.'}
                        </p>

                        <div className="flex items-center gap-3 mt-auto">
                             <input 
                                ref={fileInputRef}
                                type="file" 
                                accept=".pdf,.docx,.doc,.txt"
                                className="hidden"
                                onChange={handleFileUpload}
                              />
                             {uploadedFile ? (
                                <button
                                    onClick={() => setShowSkillsModal(true)}
                                    className="flex-1 py-2 px-4 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-mono uppercase tracking-wide border border-emerald-500/20 transition-all flex items-center justify-center gap-2"
                                >
                                    <Zap size={14} /> View Extracted Skills ({extractedSkills.length})
                                </button>
                             ) : (
                                <button 
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isUploading}
                                    className="flex-1 py-2 px-4 rounded-lg bg-white/5 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 text-xs font-mono uppercase tracking-wide border border-white/10 hover:border-cyan-500/50 transition-all flex items-center justify-center gap-2 group-hover:shadow-[0_0_15px_-5px_rgba(6,182,212,0.5)]"
                                >
                                    {isUploading ? <Loader2 className="animate-spin" size={14} /> : <><Upload size={14} /> Upload Source</>}
                                </button>
                             )}
                        </div>
                    </div>
                </motion.div>

                {/* Card 2: LinkedIn */}
                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className={`
                        relative group overflow-hidden rounded-2xl p-1 transition-all duration-500
                        ${isVerified
                            ? 'bg-gradient-to-br from-blue-500/20 via-blue-500/5 to-transparent border-blue-500/30' 
                            : 'bg-white/5 border border-white/10 hover:border-cyan-500/30'
                        }
                    `}
                >
                    <div className="relative bg-[#0a0a0f]/90 backdrop-blur-xl rounded-xl p-6 h-full border border-white/5 flex flex-col">
                         <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${isVerified ? 'bg-blue-500/10 text-blue-400' : 'bg-white/5 text-slate-400'}`}>
                                <Globe size={24} />
                            </div>
                            {isVerified && <CheckCircle size={20} className="text-blue-500" />}
                        </div>
                        
                        <h3 className="text-lg font-semibold text-white mb-1">External Profile</h3>
                        <p className="text-sm text-slate-500 mb-6 font-light flex-1">
                            {isVerified ? 'Connected to global graph.' : 'Link profile for outreach validation.'}
                        </p>

                        <div className="flex gap-2 mt-auto">
                             <div className="relative flex-1 group/input">
                                <input 
                                    className={`w-full bg-black/50 border ${verificationMsg ? 'border-red-500/50' : 'border-white/10 group-hover/input:border-cyan-500/30'} rounded-lg px-3 py-2 text-xs font-mono text-cyan-100 placeholder-slate-700 focus:outline-none focus:border-cyan-500/50 transition-all`}
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
                                className="px-4 py-2 bg-white/5 hover:bg-cyan-500/20 border border-white/10 hover:border-cyan-500/50 rounded-lg text-xs font-mono text-cyan-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                             >
                                {isVerifying ? <Loader2 size={14} className="animate-spin" /> : 'VERIFY'}
                             </button>
                        </div>
                        {verificationMsg && (
                            <p className="text-[10px] text-red-400 mt-2 font-mono">{verificationMsg}</p>
                        )}
                    </div>
                </motion.div>
            </div>
        </div>

      </div>

      {/* Skills Modal */}
      <AnimatePresence>
        {showSkillsModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowSkillsModal(false)}
              className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative bg-[#0a0a0f] border border-cyan-500/20 rounded-2xl w-full max-w-lg shadow-[0_0_50px_-10px_rgba(6,182,212,0.2)] overflow-hidden"
            >
               <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500/20 via-cyan-500 to-cyan-500/20"></div>
               
               <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
                   <h3 className="text-lg font-bold text-white flex items-center gap-2">
                       <Cpu size={18} className="text-cyan-400" /> Neural Index
                   </h3>
                   <button onClick={() => setShowSkillsModal(false)} className="hover:bg-white/10 p-1 rounded transition-colors"><X size={20} className="text-slate-400 hover:text-white" /></button>
               </div>
               
               <div className="p-6 max-h-[60vh] overflow-y-auto bg-black/40">
                    <div className="flex flex-wrap gap-2">
                    {extractedSkills.map((skill, i) => (
                        <motion.div 
                            key={i} 
                            initial={{ opacity: 0, scale: 0 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.03 }}
                            className="px-3 py-1.5 bg-cyan-500/5 hover:bg-cyan-500/10 text-cyan-400 rounded-lg text-xs font-mono border border-cyan-500/20 cursor-default"
                        >
                            {skill}
                        </motion.div>
                    ))}
                    {extractedSkills.length === 0 && <p className="text-slate-500 text-sm font-mono">No neural patterns detected.</p>}
                    </div>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
