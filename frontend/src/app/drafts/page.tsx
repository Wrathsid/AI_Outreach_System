'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Search, Mail, ArrowRight, ArrowLeft, Loader2, Brain, Linkedin, FileText } from 'lucide-react';
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
    <main className="flex-1 flex flex-col h-full overflow-x-hidden p-4 md:p-8 relative overflow-y-auto">
      <div className="max-w-[1000px] mx-auto w-full flex flex-col gap-8 pb-10">
        
        {/* Header */}
        <header className="flex flex-col gap-4">
            <FadeUp delay={0}>
                <Link href="/" className="inline-flex items-center text-slate-400 hover:text-white transition-colors mb-2 text-sm font-medium group">
                    <ArrowLeft size={16} className="mr-2 group-hover:-translate-x-1 transition-transform" />
                    Back to Dashboard
                </Link>
            </FadeUp>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                     <BlurIn delay={0.1}>
                        <h1 className="text-white text-3xl md:text-4xl font-semibold tracking-tight leading-tight">Review Drafts</h1>
                    </BlurIn>
                    <BlurIn delay={0.2}>
                         <p className="text-slate-400 mt-2 text-lg">
                            {loading ? 'Loading pending emails...' : `${drafts.length} drafts waiting for your review.`}
                         </p>
                    </BlurIn>
                </div>
            </div>
        </header>

        {/* Search & Filter */}
        <FadeUp delay={0.3} className="w-full relative z-20">
             <div className="relative group">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-50 transition-opacity duration-500 pointer-events-none"></div>
                <div className="relative flex items-center bg-black/40 border border-white/10 rounded-2xl p-2 pl-6 backdrop-blur-xl shadow-2xl ring-1 ring-white/5 focus-within:ring-primary/50 transition-all duration-300">
                    <Search className="text-slate-500" size={20} />
                    <input 
                        type="text" 
                        placeholder="Filter by name, company, or role..." 
                        value={draftSearch}
                        onChange={(e) => setDraftSearch(e.target.value)}
                        className="w-full bg-transparent border-none text-white placeholder-slate-500 focus:outline-none focus:ring-0 px-4 py-2 h-10"
                    />
                </div>
            </div>
        </FadeUp>

        {/* Drafts Grid */}
        <div className="grid grid-cols-1 gap-4">
            {loading ? (
                <div className="flex items-center justify-center p-20">
                    <div className="flex flex-col items-center gap-4">
                        <Loader2 className="animate-spin text-primary" size={32} />
                        <p className="text-slate-500">Loading your drafts...</p>
                    </div>
                </div>
            ) : filteredDrafts.length > 0 ? (
                filteredDrafts.map((draft, index) => {
                     const isLinkedIn = !draft.subject;
                     return (
                        <FadeUp key={draft.id} delay={0.4 + (index * 0.05)}>
                             <Link href={`/candidates/${draft.candidate_id}`}>
                                <motion.div 
                                    className={`group relative overflow-hidden rounded-2xl border p-6 transition-all hover:shadow-2xl ${
                                        isLinkedIn 
                                            ? 'bg-blue-950/10 border-blue-500/20 hover:border-blue-500/40 hover:bg-blue-900/20' 
                                            : 'bg-emerald-950/10 border-emerald-500/20 hover:border-emerald-500/40 hover:bg-emerald-900/20'
                                    }`}
                                    whileHover={{ scale: 1.01, y: -2 }}
                                    whileTap={{ scale: 0.99 }}
                                >
                                     {/* Hover Gradient */}
                                    <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-linear-to-r ${isLinkedIn ? 'from-blue-500 to-transparent' : 'from-emerald-500 to-transparent'}`} />

                                    <div className="flex justify-between items-start relative z-10">
                                        <div className="flex items-start gap-4">
                                            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border shadow-lg ${
                                                isLinkedIn ? 'bg-blue-500/20 border-blue-500/30 text-blue-400' : 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'
                                            }`}>
                                                {isLinkedIn ? <span className="font-bold text-lg">in</span> : <Mail size={20} />}
                                            </div>
                                            
                                            <div>
                                                <h3 className="text-white font-semibold text-lg flex items-center gap-2">
                                                    {draft.candidate_name || 'Unknown'}
                                                    {/* Status Badge */}
                                                    {draft.email_source === 'verified' ? (
                                                        <span className="text-xs px-2 py-0.5 rounded-full border bg-green-500/10 border-green-500/20 text-green-400 flex items-center gap-1">
                                                            <Mail className="w-3 h-3" />
                                                            Email
                                                        </span>
                                                    ) : draft.email_source === 'generated' ? (
                                                        <span className="text-xs px-2 py-0.5 rounded-full border bg-yellow-500/10 border-yellow-500/20 text-yellow-400 flex items-center gap-1" title="AI-inferred email • Verify before sending">
                                                            <Brain className="w-3 h-3" />
                                                            Generated
                                                        </span>
                                                    ) : !draft.subject ? (
                                                        <span className="text-xs px-2 py-0.5 rounded-full border bg-blue-500/10 border-blue-500/20 text-blue-400 flex items-center gap-1">
                                                            <Linkedin className="w-3 h-3" />
                                                            LinkedIn
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs px-2 py-0.5 rounded-full border bg-orange-500/10 border-orange-500/20 text-orange-400 flex items-center gap-1">
                                                            <FileText className="w-3 h-3" />
                                                            Draft Only
                                                        </span>
                                                    )}
                                                </h3>
                                                <p className="text-slate-400 text-sm mt-1">{draft.candidate_title} <span className="text-slate-600 mx-1">•</span> {draft.candidate_company}</p>
                                                
                                                <div className="mt-4 max-w-2xl">
                                                     {draft.subject && <p className="text-slate-200 font-medium mb-1">{draft.subject}</p>}
                                                     <p className="text-slate-400 text-sm leading-relaxed line-clamp-2 md:line-clamp-3 opacity-90 group-hover:opacity-100 transition-opacity">
                                                        {draft.body}
                                                     </p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex flex-col items-end gap-2">
                                            <div className={`p-3 rounded-full transition-all duration-300 ${isLinkedIn ? 'bg-blue-500/10 text-blue-400 group-hover:bg-blue-500 group-hover:text-white' : 'bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500 group-hover:text-white'}`}>
                                                <ArrowRight size={20} className="-rotate-45 group-hover:rotate-0 transition-transform duration-300" />
                                            </div>
                                            <span className="text-xs text-slate-500 mt-2 font-medium group-hover:text-white transition-colors">Review</span>
                                        </div>
                                    </div>
                                </motion.div>
                             </Link>
                        </FadeUp>
                     );
                })
            ) : (
                 <FadeUp delay={0.4}>
                    <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/5">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-500">
                             <Mail size={32} />
                        </div>
                        <h3 className="text-white text-lg font-medium mb-1">No drafts found</h3>
                        <p className="text-slate-500">
                            {draftSearch ? `No results for "${draftSearch}"` : "You're all caught up! Go find some new leads."}
                        </p>
                        {!draftSearch && (
                            <Link href="/search" className="inline-block mt-6 px-6 py-3 bg-primary hover:bg-blue-600 text-white rounded-xl font-medium transition-colors">
                                Find Leads
                            </Link>
                        )}
                    </div>
                </FadeUp>
            )}
        </div>

      </div>
    </main>
  );
}
