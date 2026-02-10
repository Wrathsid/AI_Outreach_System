'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { 
  Briefcase, MapPin, Linkedin, 
  Mail, ChevronDown, ChevronUp,
  Copy, Send, ExternalLink, ArrowLeft, Trash2,
  Loader2
} from 'lucide-react';
import { api, Candidate, Draft } from '@/lib/api';
import { cleanDisplayName } from '@/lib/displayUtils';
import { useToast } from '@/context/ToastContext';
import { triggerConfetti } from '@/lib/confetti';

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

  // Editor State
  // Multi-Channel State
  const [activeTab, setActiveTab] = useState<'email' | 'linkedin'>('email');
  const [emailDraft, setEmailDraft] = useState<Draft | null>(null);
  const [linkedinDraft, setLinkedinDraft] = useState<Draft | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);

  // Editor State (Derived from active tab, but we keep synced for rendering)
  // We'll use refs or just simple state updates on tab switch
  // Actually, let's keep one "edited" state that syncs when tabs change, or separate?
  // Simpler: Keep separate edited states to persist changes when switching tabs.
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [linkedinBody, setLinkedinBody] = useState('');

  // Context State
  const [showContext, setShowContext] = useState(false);

  const generateContent = useCallback((type: 'email' | 'linkedin') => {
      setIsGenerating(true);
      api.generateDraft(candidateId, '', type).then(newDraft => {
          if (newDraft) {
             const draftData: Draft = {
                 id: newDraft.draft_id || 0,
                 candidate_id: candidateId,
                 subject: newDraft.subject || '',
                 body: (newDraft.message || newDraft.body) || '',
                 status: 'draft'
             };

             if (type === 'email') {
                 setEmailDraft(draftData);
                 setEmailSubject(draftData.subject);
                 setEmailBody(draftData.body);
             } else {
                 setLinkedinDraft(draftData);
                 setLinkedinBody(draftData.body);
             }
             success(`Generated ${type === 'email' ? 'email' : 'connection message'}`);
          }
          setIsGenerating(false);
      }).catch(() => setIsGenerating(false));
  }, [candidateId, success]);

  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
        setLoading(true);
        try {
            const [candidateData, draftsData] = await Promise.all([
                api.getCandidate(candidateId),
                api.getDrafts()
            ]);
            
            if (mounted && candidateData) {
                setCandidate(candidateData);
                
                const hasEmail = candidateData.email || candidateData.generated_email;
                const initialTab = hasEmail ? 'email' : 'linkedin';
                setActiveTab(initialTab);

                const eDraft = draftsData.find((d: Draft) => d.candidate_id === candidateId && d.subject);
                const lDraft = draftsData.find((d: Draft) => d.candidate_id === candidateId && !d.subject);
                
                if (eDraft) {
                    setEmailDraft(eDraft);
                    setEmailSubject(eDraft.subject);
                    setEmailBody(eDraft.body);
                }
                if (lDraft) {
                    setLinkedinDraft(lDraft);
                    setLinkedinBody(lDraft.body);
                }

                // Auto-Generate if missing for INITIAL tab
                // Note: We use the local vars eDraft/lDraft here
                if (initialTab === 'email' && !eDraft) {
                    generateContent('email');
                } else if (initialTab === 'linkedin' && !lDraft) {
                    generateContent('linkedin');
                }
            }
        } catch (err) {
            console.error(err);
        } finally {
            if (mounted) setLoading(false);
        }
    };

    loadData();

    return () => { mounted = false; };
  }, [candidateId, generateContent]);

  const handleDelete = async () => {
    if (confirm('Delete this candidate?')) {
      await api.deleteCandidate(candidateId);
      router.push('/');
    }
  };

  const handleAction = async () => {
    if (!candidate) return;

    if (activeTab === 'linkedin') {
       navigator.clipboard.writeText(linkedinBody);
       
       // POST-SEND FEEDBACK (Priority 7)
       success("✅ Copied to clipboard. Marked as contacted.");
       
       // UX Improvement: Track sent (for Sent page)
       await api.markAsSent(candidateId);

       // OPTIONAL: Launch Automation
       // We could auto-launch here, but let's keep it manual via the button for now.
       return;
    }



    // Email Mode
    if (!emailBody) return error("Message is empty");
    setIsSending(true);
    const sent = await api.sendEmail(
        candidate.email || candidate.generated_email || '', 
        emailSubject, 
        emailBody, 
        candidate.id
    );
    
    if (sent) {
       // POST-SEND FEEDBACK (Priority 7)
       success("✅ Email sent. Marked as contacted.");
       triggerConfetti();
       
       // UX Improvement: Track sent (for Sent page)
       await api.markAsSent(candidateId);
    } else {
       error("Failed to send");
    }
    setIsSending(false);
  };

  const handleLaunchAutomation = async () => {
      if (!linkedinBody) return error("Generate a draft first");
      
      const confirmLaunch = window.confirm("🚀 Launch Browser Automation?\n\nThis will:\n1. Open Chrome (using your profile)\n2. Go to LinkedIn\n3. Click Connect\n4. Paste the message\n\nIt will STOP before sending so you can review.");
      if (!confirmLaunch) return;

      success("Launching Automation...");
      try {
          const res = await api.launchAutomation(candidateId);
          if (res.status === 'success') {
              success("✅ Automation Complete! Check the Chrome window.");
          } else {
              if (res.status === 'pending') {
                  success("⚠️ Connection already pending.");
              } else {
                  error("Automation finished with warnings. Check logs.");
              }
          }
      } catch (err) {
          error("Failed to launch automation");
      }
  };
  
  const handleTabSwitch = (tab: 'email' | 'linkedin') => {
      setActiveTab(tab);
      // Auto-generate if switching to a tab that has no content
      if (tab === 'email' && !emailBody && !emailDraft) {
          generateContent('email');
      } else if (tab === 'linkedin' && !linkedinBody && !linkedinDraft) {
          generateContent('linkedin');
      }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0B15]">
        <Loader2 className="animate-spin text-slate-500" size={24} />
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
            onClick={() => router.push('/')} 
            className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors text-sm"
        >
            <ArrowLeft size={16} />
            <span className="font-medium">Candidates</span>
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
                <h1 className="text-3xl font-bold text-white tracking-tight leading-tight">
                    {cleanDisplayName(candidate.name)}
                </h1>
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

            {/* Contact Actions */}
            <div className="space-y-3 pt-4 border-t border-white/5">
                <div className="flex items-center justify-between group">
                    <div className="flex items-center gap-3 text-sm">
                        <Mail size={16} className={hasEmail ? "text-slate-300" : "text-slate-600"} />
                        <span className={hasEmail ? "text-slate-200" : "text-slate-600 italic"}>
                            {hasEmail ? (candidate.email || candidate.generated_email) : 'No email found'}
                        </span>
                    </div>
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

            {/* Collapsible Context */}
            <div className="pt-4 border-t border-white/5">
                <button 
                    onClick={() => setShowContext(!showContext)}
                    className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-300 transition-colors"
                >
                    {showContext ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    Context & Notes
                </button>
                
                {showContext && (
                    <div className="mt-4 space-y-4 animate-in slide-in-from-top-2 duration-200">
                        {candidate.summary ? (
                            <p className="text-sm text-slate-400 leading-relaxed bg-[#131326] p-4 rounded-xl border border-white/5">
                                {candidate.summary}
                            </p>
                        ) : (
                            <p className="text-xs text-slate-600 italic">No context available.</p>
                        )}
                    </div>
                )}
            </div>
        </div>

        {/* Right Column: Writing Area (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col h-[calc(100vh-140px)] min-h-[500px]">
            <MinimalCard className="flex-1 flex flex-col p-1 overflow-hidden bg-[#0f0f15]">
                
                {/* Editor Header & Tabs */}
                <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between min-h-[70px]">
                     {hasEmail && candidate.linkedin_url ? (
                         <div className="flex items-center gap-1 bg-[#131326] p-1 rounded-lg border border-white/5">
                             <button
                                onClick={() => handleTabSwitch('email')}
                                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'email' ? 'bg-[#0f0f15] text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
                             >
                                Email
                             </button>
                             <button
                                onClick={() => handleTabSwitch('linkedin')}
                                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${activeTab === 'linkedin' ? 'bg-[#0077b5]/10 text-[#0077b5] shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
                             >
                                <Linkedin size={12} />
                                LinkedIn
                             </button>
                         </div>
                     ) : (
                        <h2 className="font-medium text-white">
                            {hasEmail ? 'Compose Email' : 'Connection Message'}
                        </h2>
                     )}
                     
                    {activeTab === 'email' && (
                         <span className="text-xs text-slate-500">Draft saved locally</span>
                    )}

                    {/* View Post Button (Contextual) */}
                    {(candidate.linkedin_url?.includes('/posts/') || candidate.linkedin_url?.includes('/feed/') || candidate.linkedin_url?.includes('/activity/')) && (
                       <a 
                           href={candidate.linkedin_url}
                           target="_blank" 
                           rel="noopener noreferrer"
                           className="ml-auto flex items-center gap-2 text-xs bg-[#131326] hover:bg-[#1c1c36] text-[#0077b5] px-3 py-1.5 rounded-lg border border-white/5 transition-colors"
                       >
                           <ExternalLink size={12} />
                           View Post
                       </a>
                    )}
                </div>

                {/* Subject Line (Email Only) */}
                {activeTab === 'email' && (
                    <input 
                        className="w-full bg-transparent border-b border-white/5 px-6 py-4 text-slate-200 placeholder-slate-600 focus:outline-none focus:bg-white/5 transition-colors"
                        placeholder="Subject"
                        value={emailSubject}
                        onChange={(e) => setEmailSubject(e.target.value)}
                    />
                )}

                {/* Main Textarea */}
                <textarea
                    className={`w-full bg-[#0f0f15] border border-white/5 focus:border-primary/50 rounded-2xl px-5 py-4 text-white placeholder-slate-600 focus:outline-none transition-all leading-relaxed font-sans text-sm min-h-[400px] resize-y ${isGenerating ? 'animate-pulse opacity-50 cursor-wait' : ''}`}
                    placeholder={isGenerating ? "AI is writing your message..." : (activeTab === 'email' ? "Hi [Name], I noticed..." : "Hi [Name], I'd like to connect...")}
                    value={activeTab === 'email' ? emailBody : linkedinBody}
                    onChange={(e) => activeTab === 'email' ? setEmailBody(e.target.value) : setLinkedinBody(e.target.value)}
                    disabled={isGenerating}
                />

                {/* Footer Actions */}
                <div className="px-6 py-4 border-t border-white/5 bg-[#131326]/50 flex items-center justify-between">
                     <span className="text-xs text-slate-600">
                        {(activeTab === 'email' ? emailBody : linkedinBody).length} characters
                     </span>

                     <button
                        onClick={handleAction}
                        disabled={isSending}
                        className="px-6 py-2 rounded-lg bg-white text-black hover:bg-slate-200 font-semibold text-sm transition-colors flex items-center gap-2 disabled:opacity-50"
                     >
                        {isSending ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : activeTab === 'email' ? (
                            <Send size={16} />
                        ) : (
                            <Copy size={16} />
                        )}
                        {activeTab === 'email' ? 'Send Email' : 'Copy for LinkedIn'}
                     </button>

                     {/* Automation Button */}
                     {/* Automation Button - MASKED per user request (Feb 10) */}
                     {/* 
                     {activeTab === 'linkedin' && (
                         <button
                            onClick={handleLaunchAutomation}
                            className="px-4 py-2 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 font-semibold text-sm transition-colors flex items-center gap-2 border border-blue-600/30"
                            title="Auto-open LinkedIn and paste message"
                         >
                            <Send size={16} />
                            <span>Auto-Fill</span>
                         </button>
                     )}
                     */}
                </div>
            </MinimalCard>
        </div>

      </div>
    </div>
  );
}
