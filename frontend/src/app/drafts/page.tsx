'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Search, Mail, ArrowLeft, Loader2, Brain, Linkedin, FileText, Sparkles, Send } from 'lucide-react';
import { api, Draft } from '@/lib/api';
import { FadeUp, BlurIn } from '@/components/Animations';

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [draftSearch, setDraftSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDrafts = async () => {
      try {
        const data = await api.getDrafts();
        setDrafts(data);
      } catch (error) {
        console.error('Failed to load drafts:', error);
      } finally {
        setLoading(false);
      }
    };
    loadDrafts();
  }, []);

  const filteredDrafts = drafts.filter(d => {
    if (!draftSearch) return true;
    const term = draftSearch.toLowerCase();
    return (
        d.candidate_name?.toLowerCase().includes(term) ||
        d.candidate_company?.toLowerCase().includes(term) ||
        d.candidate_title?.toLowerCase().includes(term) ||
        d.subject.toLowerCase().includes(term)
    );
  });

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden p-0 relative bg-[#0a0a0f]">
       {/* Ambient Backlight */}
       <div className="fixed inset-0 pointer-events-none z-0">
            <div className="absolute top-[10%] right-[10%] w-[40%] h-[40%] rounded-full bg-emerald-600/5 blur-[120px]"></div>
            <div className="absolute bottom-[10%] left-[10%] w-[40%] h-[40%] rounded-full bg-blue-600/5 blur-[100px]"></div>
       </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 z-10">
        <div className="max-w-[1000px] mx-auto w-full flex flex-col gap-8 pb-10">
            
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-white/5 pb-6">
                <div className="flex flex-col gap-2">
                    <Link href="/" className="inline-flex items-center text-slate-400 hover:text-white transition-colors text-sm font-medium group w-fit">
                        <ArrowLeft size={16} className="mr-2 group-hover:-translate-x-1 transition-transform" />
                        Back to Dashboard
                    </Link>
                    <BlurIn delay={0.1}>
                        <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight flex items-center gap-3">
                            <span className="p-2 bg-linear-to-br from-emerald-500/20 to-teal-500/20 rounded-xl border border-white/10 text-emerald-400">
                                <FileText size={28} />
                            </span>
                            Drafts Review
                        </h1>
                    </BlurIn>
                    <BlurIn delay={0.2}>
                         <p className="text-slate-400 text-lg">
                            {loading ? 'Syncing...' : `${drafts.length} drafts ready for approval`}
                         </p>
                    </BlurIn>
                </div>
                
                {/* Search Bar */}
                <FadeUp delay={0.2} className="w-full md:w-auto min-w-[300px]">
                     <div className="relative group">
                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-30 transition-opacity duration-500 pointer-events-none"></div>
                        <div className="relative flex items-center bg-white/5 border border-white/10 rounded-xl p-2 pl-4 backdrop-blur-md focus-within:ring-2 focus-within:ring-primary/50 focus-within:bg-white/10 transition-all duration-300">
                            <Search className="text-slate-500" size={18} />
                            <input 
                                type="text" 
                                placeholder="Search drafts..." 
                                value={draftSearch}
                                onChange={(e) => setDraftSearch(e.target.value)}
                                className="w-full bg-transparent border-none text-white placeholder-slate-500 focus:outline-none focus:ring-0 px-3 py-1.5 h-9 text-sm"
                            />
                        </div>
                    </div>
                </FadeUp>
            </header>

            {/* Grid */}
            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-32 gap-4">
                        <div className="p-4 rounded-full bg-white/5 animate-pulse">
                            <Loader2 className="animate-spin text-primary" size={32} />
                        </div>
                        <p className="text-slate-500 font-medium">Loading your drafts...</p>
                    </div>
                ) : filteredDrafts.length > 0 ? (
                    filteredDrafts.map((draft, index) => {
                         const isLinkedIn = !draft.subject;
                         return (
                            <FadeUp key={draft.id} delay={index * 0.05}>
                                 <Link href={`/candidates/${draft.candidate_id}`}>
                                    <motion.div 
                                        className="group relative overflow-hidden rounded-2xl border border-white/5 bg-[#16161a] p-6 transition-all hover:bg-[#1c1c21]"
                                        whileHover={{ y: -2, boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)' }}
                                        whileTap={{ scale: 0.995 }}
                                    >
                                         <div className={`absolute left-0 top-0 bottom-0 w-1 ${isLinkedIn ? 'bg-blue-500' : 'bg-emerald-500'} opacity-50 group-hover:opacity-100 transition-opacity`} />
                                         
                                         {/* Top glow */}
                                        <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-linear-to-r ${isLinkedIn ? 'from-blue-500/30 to-transparent' : 'from-emerald-500/30 to-transparent'}`} />

                                        <div className="flex justify-between items-start relative z-10 gap-6">
                                            <div className="flex items-start gap-5">
                                                <div className="relative">
                                                     <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border shadow-lg shrink-0 ${
                                                        isLinkedIn ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                                    }`}>
                                                        {isLinkedIn ? <Linkedin size={24} /> : <Mail size={24} />}
                                                    </div>
                                                    {draft.match_score && (
                                                        <div className="absolute -bottom-2 -right-2 bg-[#0f0f12] px-1.5 py-0.5 rounded-md border border-white/10 text-[10px] font-bold text-slate-300 shadow-sm">
                                                            {draft.match_score}%
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <h3 className="text-white font-semibold text-lg truncate group-hover:text-primary transition-colors">
                                                            {draft.candidate_name || 'Unknown Candidate'}
                                                        </h3>
                                                        <div className="flex items-center gap-2">
                                                            {draft.email_source === 'verified' && (
                                                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 font-medium">Verified</span>
                                                            )}
                                                            {draft.email_source === 'generated' && (
                                                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 font-medium flex items-center gap-1">
                                                                    <Brain size={10} /> AI Guessed
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                    
                                                    <p className="text-slate-400 text-sm flex items-center gap-2 mb-4">
                                                        <span className="truncate max-w-[200px]">{draft.candidate_title}</span>
                                                        <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                                                        <span className="truncate max-w-[200px] text-slate-300">{draft.candidate_company}</span>
                                                    </p>
                                                    
                                                    <div className="pl-4 border-l-2 border-white/5 py-1">
                                                         {draft.subject && <p className="text-slate-200 font-medium text-sm mb-1 line-clamp-1">{draft.subject}</p>}
                                                         <p className="text-slate-500 text-sm leading-relaxed line-clamp-2 md:line-clamp-2 font-mono opacity-80 group-hover:opacity-100 transition-opacity">
                                                            {draft.body}
                                                         </p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex flex-col items-end gap-3 self-center">
                                                <div className={`p-3 rounded-xl transition-all duration-300 flex items-center gap-2 pr-4 pl-3 group/btn ${isLinkedIn ? 'bg-blue-500/10 text-blue-400 hover:bg-blue-600 hover:text-white' : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-600 hover:text-white'}`}>
                                                    <Send size={18} className="group-hover/btn:translate-x-1 transition-transform" />
                                                    <span className="text-sm font-medium">Review</span>
                                                </div>
                                                <span className="text-xs text-slate-600 font-mono">
                                                    {new Date(draft.created_at || Date.now()).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                    </motion.div>
                                 </Link>
                            </FadeUp>
                         );
                    })
                ) : (
                     <FadeUp delay={0.2}>
                        <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
                            <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mb-6 ring-2 ring-white/5">
                                 <Sparkles size={32} className="text-slate-600" />
                            </div>
                            <h3 className="text-white text-xl font-medium mb-2">Each draft is a possibility</h3>
                            <p className="text-slate-500 max-w-md mx-auto mb-8">
                                {draftSearch ? `No drafts found matching "${draftSearch}"` : "You haven't generated any drafts yet. Start a search to find leads and let AI write the first message."}
                            </p>
                            {!draftSearch && (
                                <Link href="/search" className="px-8 py-3 bg-primary hover:bg-blue-600 text-white rounded-full font-medium transition-all shadow-lg hover:shadow-primary/25 hover:scale-105 active:scale-95 flex items-center gap-2">
                                    <Search size={18} />
                                    Find New Leads
                                </Link>
                            )}
                        </div>
                    </FadeUp>
                )}
            </div>
        </div>
      </div>
    </main>
  );
}
