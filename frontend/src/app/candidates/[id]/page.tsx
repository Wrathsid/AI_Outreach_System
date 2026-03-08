'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  Briefcase, MapPin, Linkedin, 
  Mail,
  Copy, ExternalLink, ArrowLeft, Trash2,
  Check, Sparkles, ChevronDown
} from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { cleanDisplayName } from '@/lib/displayUtils';
import { useToast } from '@/context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { CandidateProfileSkeleton } from '@/components/SkeletonLoaders';

// --- Shared Components ---

const MinimalCard = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
  <div className={`bg-[#131326] border border-white/5 rounded-2xl ${className}`}>
    {children}
  </div>
);

export default function MinimalCandidatePage() {
  const router = useRouter();
  const params = useParams();
  const candidateId = Number(params.id);
  
  const { success, error } = useToast();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);

  // Status dropdown state
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);

  const handleStatusChange = async (newStatus: 'new' | 'contacted') => {
    if (!candidate) return;
    
    // Optimistic UI update
    const previousStatus = candidate.status;
    setCandidate({ ...candidate, status: newStatus });
    setIsStatusDropdownOpen(false);
    
    const updateSuccess = await api.updateCandidateStatus(candidate.id, newStatus);
    if (!updateSuccess) {
      // Revert on failure
      setCandidate({ ...candidate, status: previousStatus });
      error('Failed to update status');
    } else {
      success(`Marked as ${newStatus === 'contacted' ? 'Contacted' : 'Non-contacted'}`);
      router.refresh();
    }
  };

  // LinkedIn message state
  const [linkedinBody, setLinkedinBody] = useState('');
  const [originalLinkedinBody, setOriginalLinkedinBody] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  // Debounce guard for generation
  const lastGenerateRef = useRef<number>(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);


  const generateLinkedinMessage = useCallback(() => {
      const now = Date.now();
      if (now - lastGenerateRef.current < 2000) return;
      lastGenerateRef.current = now;

      setIsGenerating(true);
      api.generateDraft(candidateId, '', 'linkedin').then(newDraft => {
          if (newDraft) {
              const draftedText = (newDraft.message || newDraft.body) || '';
              setLinkedinBody(draftedText);
              setOriginalLinkedinBody(draftedText);
              setTimeout(() => success('Generated connection message'), 150); // Defer for UI thread
          }
          setIsGenerating(false);
      }).catch(() => setIsGenerating(false));
  }, [candidateId, success]);

  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
        setLoading(true);
        try {
            const candidateData = await api.getCandidate(candidateId);
            
            if (mounted && candidateData) {
                setCandidate(candidateData);
                
                // Auto-generate LinkedIn message
                generateLinkedinMessage();
            }
        } catch (err) {
            console.error(err);
        } finally {
            if (mounted) setLoading(false);
        }
    };

    loadData();

    return () => { mounted = false; };
  }, [candidateId, generateLinkedinMessage]);

  const handleDelete = async () => {
    if (confirm('Delete this candidate?')) {
      await api.deleteCandidate(candidateId);
      router.push('/candidates');
    }
  };

  const handleCopyMessage = async () => {
    if (!linkedinBody) return error("Message is empty");
    
    // RAG: Save edit if user modified the text manually before copying
    if (linkedinBody !== originalLinkedinBody && originalLinkedinBody !== '') {
        try {
            await api.saveDraftEdit(candidateId, originalLinkedinBody, linkedinBody, 'linkedin');
        } catch (err) {
            console.error('Quietly failing RAG edit save', err);
        }
    }
    
    navigator.clipboard.writeText(linkedinBody);
    
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    
    await api.updateCandidateStatus(candidateId, 'contacted');
    
    // Optimistic local update
    setCandidate(prev => prev ? { ...prev, status: 'contacted' } : null);
    
    success("✅ Copied to clipboard. Marked as contacted.");
    router.refresh();
  };

  if (loading) {
    return (
      <div className="flex-1 w-full min-h-screen bg-[#0B0B15] text-slate-300 font-sans">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <button 
              onClick={() => router.push('/candidates')} 
              className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors text-sm"
          >
              <ArrowLeft size={16} />
              <span className="font-medium">Pipeline</span>
          </button>
        </div>
        <CandidateProfileSkeleton />
      </div>
    );
  }

  if (!candidate) return null;

  const hasEmail = candidate.email || candidate.generated_email;

  return (
    <div className="flex-1 w-full min-h-screen bg-[#0B0B15] text-slate-300 font-sans selection:bg-white/10 selection:text-white">
      
      {/* Minimal Header */}
      <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
        <button 
            onClick={() => router.push('/candidates')} 
            className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors text-sm"
        >
            <ArrowLeft size={16} />
            <span className="font-medium">Pipeline</span>
        </button>
        <button 
            onClick={handleDelete}
            className="text-slate-600 hover:text-red-400 transition-colors"
        >
            <Trash2 size={16} />
        </button>
      </div>

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* Left Column: Context & Contact (4 Cols) */}
        <div className="lg:col-span-4 space-y-8">
            
            {/* Profile Header */}
            <div className="space-y-4">
                <div className="flex items-start justify-between gap-4">
                    <h1 className="text-3xl font-bold text-white tracking-tight leading-tight">
                        {cleanDisplayName(candidate.name)}
                    </h1>
                    
                    {/* Status Dropdown */}
                    <div className="relative hidden lg:block"> {/* Keep it right-aligned explicitly */}
                        <button 
                            onClick={() => setIsStatusDropdownOpen(!isStatusDropdownOpen)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                                candidate.status === 'contacted' 
                                ? 'bg-orange-500/10 text-orange-400 border-orange-500/20 hover:bg-orange-500/20' 
                                : 'bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20'
                            }`}
                        >
                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                            {candidate.status === 'contacted' ? 'Contacted' : 'Non-contacted'}
                            <ChevronDown size={14} className={`transition-transform ${isStatusDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                        
                        <AnimatePresence>
                            {isStatusDropdownOpen && (
                                <motion.div 
                                    initial={{ opacity: 0, y: 5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 5 }}
                                    className="absolute right-0 mt-2 w-40 bg-[#1A1A2E] border border-white/10 rounded-xl shadow-xl overflow-hidden z-50 py-1"
                                >
                                    <button
                                        onClick={() => handleStatusChange('new')}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors flex items-center justify-between"
                                    >
                                        Non-contacted
                                        {candidate.status !== 'contacted' && <Check size={14} className="text-blue-400" />}
                                    </button>
                                    <button
                                        onClick={() => handleStatusChange('contacted')}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors flex items-center justify-between"
                                    >
                                        Contacted
                                        {candidate.status === 'contacted' && <Check size={14} className="text-orange-400" />}
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
                <div className="space-y-1 text-sm text-slate-400">
                    {candidate.title && (
                        <div className="flex items-center gap-2">
                            <Briefcase size={14} className="text-slate-500" />
                            <span>{candidate.title}</span>
                        </div>
                    )}
                    {candidate.company && (
                        <div className="pl-6 text-slate-500">
                             at {candidate.company}
                        </div>
                    )}
                    {candidate.location && (
                        <div className="flex items-center gap-2">
                            <MapPin size={14} className="text-slate-500" />
                            <span>{candidate.location}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Contact Info */}
            <div className="space-y-3 pt-4 border-t border-white/5">
                {/* Email - display only, no compose */}
                <div className="flex items-center justify-between group">
                    <div className="flex items-center gap-3 text-sm">
                        <Mail size={16} className={hasEmail ? "text-slate-300" : "text-slate-600"} />
                        <span className={hasEmail ? "text-slate-200" : "text-slate-600 italic"}>
                            {hasEmail ? (candidate.email || candidate.generated_email) : 'No email found'}
                        </span>
                    </div>
                    {hasEmail && (
                        <button
                            onClick={() => {
                                navigator.clipboard.writeText(candidate.email || candidate.generated_email || '');
                                success('Email copied to clipboard');
                            }}
                            className="text-slate-600 hover:text-white transition-colors p-1 rounded hover:bg-white/5"
                            title="Copy email"
                        >
                            <Copy size={14} />
                        </button>
                    )}
                </div>

                {candidate.linkedin_url && (
                    <a 
                        href={candidate.linkedin_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 text-sm text-[#0077b5] hover:text-[#00669c] transition-colors"
                    >
                        {candidate.linkedin_url.includes('/posts/') || candidate.linkedin_url.includes('/feed/') || candidate.linkedin_url.includes('/activity/') ? (
                             <>
                                <ExternalLink size={16} />
                                <span className="font-medium">View Post</span>
                             </>
                        ) : (
                             <>
                                <Linkedin size={16} />
                                <span className="font-medium">Open LinkedIn Profile</span>
                             </>
                        )}
                        <ExternalLink size={12} className="opacity-50" />
                    </a>
                )}
            </div>

            {/* Failure Visibility (UX Trust Pattern) */}
            {candidate.status === 'contacted' && candidate.sent_at && (
                (() => {
                    const daysAgo = Math.floor((new Date().getTime() - new Date(candidate.sent_at).getTime()) / (1000 * 3600 * 24));
                    if (daysAgo > 7) {
                        return (
                            <div className="bg-white/5 rounded-lg p-3 border border-white/5 flex gap-3 animate-in fade-in duration-500">
                                <span className="text-xl">🤷‍♂️</span>
                                <div>
                                    <p className="text-xs font-semibold text-slate-300">No reply yet? That&apos;s normal.</p>
                                    <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                                        Most replies come from follow-ups. Try a &quot;lighter&quot; touch for the next one.
                                    </p>
                                </div>
                            </div>
                        );
                    }
                    return null;
                })()
            )}



        </div>

        {/* Right Column: LinkedIn Message (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col h-[calc(100vh-140px)] min-h-[500px]">
            <MinimalCard className="flex-1 flex flex-col p-1 overflow-hidden bg-[#0f0f15]">
                
                {/* Editor Header */}
                <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between min-h-[70px]">
                     <div className="flex items-center gap-3">
                         <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0077b5]/10 text-[#0077b5] text-sm font-medium">
                             <Linkedin size={14} />
                             LinkedIn Message
                         </div>
                     </div>

                     <div className="flex items-center gap-2">
                         {/* Regenerate Button */}
                         <button
                             onClick={generateLinkedinMessage}
                             disabled={isGenerating}
                             className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 border border-white/5 transition-colors disabled:opacity-50"
                         >
                             <Sparkles size={12} />
                             Regenerate
                         </button>

                         {/* View Post Button (Contextual) */}
                         {(candidate.linkedin_url?.includes('/posts/') || candidate.linkedin_url?.includes('/feed/') || candidate.linkedin_url?.includes('/activity/')) && (
                            <a 
                                href={candidate.linkedin_url}
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-xs bg-[#131326] hover:bg-[#1c1c36] text-[#0077b5] px-3 py-1.5 rounded-lg border border-white/5 transition-colors"
                            >
                                <ExternalLink size={12} />
                                View Post
                            </a>
                         )}
                     </div>
                </div>

                {/* Main Textarea */}
                <div className="relative flex-1">
                  <textarea
                    ref={textareaRef}
                    className={`w-full h-full bg-[#0f0f15] border border-white/5 focus:border-primary/50 rounded-2xl px-6 py-5 text-white placeholder-slate-600 focus:outline-none transition-all leading-[1.85] font-sans text-sm min-h-[400px] resize-y ${isGenerating ? 'opacity-30' : ''}`}
                    placeholder="Hi [Name], I'd like to connect..."
                    value={linkedinBody}
                    onChange={(e) => {
                      const pos = e.target.selectionStart;
                      setLinkedinBody(e.target.value);
                      requestAnimationFrame(() => {
                        if (textareaRef.current) {
                          textareaRef.current.selectionStart = pos;
                          textareaRef.current.selectionEnd = pos;
                        }
                      });
                    }}
                    disabled={isGenerating}
                  />
                  {isGenerating && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="flex items-center gap-1.5">
                          {[0, 1, 2].map((i) => (
                            <motion.div
                              key={i}
                              className="w-2.5 h-2.5 rounded-full bg-primary"
                              animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
                              transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
                            />
                          ))}
                        </div>
                        <span className="text-xs text-slate-500 font-medium animate-pulse">AI is crafting your message...</span>
                      </div>
                    </div>
                  )}
                </div>


                {/* Footer Actions */}
                <div className="px-6 py-4 border-t border-white/5 bg-[#131326]/50 flex items-center justify-between">
                     {/* Character count */}
                     {(() => {
                       const len = linkedinBody.length;
                       const limit = 1000;
                       const color = len <= limit ? 'bg-green-400' : 'bg-red-400';
                       return (
                         <span className="flex items-center gap-2 text-xs text-slate-600">
                             <span className={`w-1.5 h-1.5 rounded-full ${color} inline-block`} />
                             {len} / {limit} chars
                         </span>
                       );
                     })()}

                     <button
                        onClick={handleCopyMessage}
                        className="px-6 py-2 rounded-lg bg-white text-black hover:bg-slate-200 font-semibold text-sm transition-colors flex items-center gap-2 disabled:opacity-50 min-w-[160px] justify-center overflow-hidden relative group"
                     >
                        <AnimatePresence mode="popLayout" initial={false}>
                          {copied ? (
                            <motion.div
                              key="check"
                              initial={{ opacity: 0, scale: 0.5, y: -10 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.5, y: 10 }}
                              transition={{ duration: 0.2, type: "spring", stiffness: 300, damping: 20 }}
                              className="flex items-center gap-2 text-green-600"
                            >
                              <Check size={16} strokeWidth={3} />
                              <span>Copied!</span>
                            </motion.div>
                          ) : (
                            <motion.div
                              key="copy"
                              initial={{ opacity: 0, scale: 0.5, y: -10 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.5, y: 10 }}
                              transition={{ duration: 0.2, type: "spring", stiffness: 300, damping: 20 }}
                              className="flex items-center gap-2"
                            >
                              <Copy size={16} />
                              <span>Copy for LinkedIn</span>
                            </motion.div>
                          )}
                        </AnimatePresence>
                     </button>
                </div>
            </MinimalCard>
        </div>

      </div>
    </div>
  );
}
