'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { FileText, Trash2, RefreshCw, Send, ExternalLink, Sparkles, Mail, Linkedin, ChevronDown } from 'lucide-react';
import { api, Draft } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { PipelineSkeleton } from '@/components/SkeletonLoaders';
import { FadeUp } from '@/components/Animations';

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  pending: { bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-400', label: 'Pending' },
  sent: { bg: 'bg-green-500/10', text: 'text-green-400', dot: 'bg-green-400', label: 'Sent' },
  replied: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400', label: 'Replied' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-400', label: 'Failed' },
};

const DraftsPage = () => {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { success: successToast, error: errorToast } = useToast();

  const loadDrafts = async () => {
    setLoading(true);
    try {
      const data = await api.getDrafts();
      setDrafts(data);
    } catch (error) {
      console.error("Failed to load drafts", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, []);

  const handleDeleteAll = async () => {
    if (!window.confirm('Delete all drafts? This cannot be undone.')) return;
    setLoading(true);
    const success = await api.deleteAllDrafts();
    if (success) {
      setDrafts([]);
      successToast('All drafts deleted');
    } else {
      errorToast('Failed to delete drafts');
    }
    setLoading(false);
  };

  // Count by status
  const counts = React.useMemo(() => {
    const c: Record<string, number> = { pending: 0, sent: 0, replied: 0, failed: 0 };
    drafts.forEach(d => { c[d.status || 'pending'] = (c[d.status || 'pending'] || 0) + 1; });
    return c;
  }, [drafts]);

  const filteredDrafts = React.useMemo(() => {
    const list = filter === 'all' ? drafts : drafts.filter(d => (d.status || 'pending') === filter);
    return [...list].sort((a, b) => b.id - a.id);
  }, [drafts, filter]);

  return (
    <main className="flex-1 h-full overflow-y-auto overflow-x-hidden flex flex-col relative w-full bg-[#0a0a0f]">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-violet-600/5 blur-[120px] animate-ambient-drift" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/5 blur-[100px] animate-ambient-drift-slow" />
      </div>

      {/* Header */}
      <header className="px-6 md:px-8 py-5 flex justify-between items-center border-b border-white/5 bg-[#0f0f12]/50 backdrop-blur-md z-10 shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
            <FileText size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Drafts
              <span className="text-slate-500 font-normal text-base">/ {drafts.length} Messages</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDeleteAll}
            className="p-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium mr-2"
            title="Delete All Drafts"
          >
            <Trash2 size={16} />
            <span className="hidden sm:inline">Delete All</span>
          </button>
          <button
            onClick={loadDrafts}
            className={`p-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      {/* Filter Bar */}
      <div className="px-6 md:px-8 py-4 z-10 shrink-0">
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/5">
          {[
            { key: 'all', label: 'All' },
            { key: 'pending', label: 'Pending' },
            { key: 'sent', label: 'Sent' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === key
                  ? 'bg-white/10 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              {label}
              <span className="ml-1.5 text-xs opacity-60">
                {key === 'all' ? drafts.length : (counts[key] || 0)}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Draft List */}
      <div className="flex-1 px-6 md:px-8 pb-8 z-10">
        <div className="max-w-[900px] mx-auto space-y-2">
          {loading ? (
            <PipelineSkeleton />
          ) : filteredDrafts.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                <FileText size={24} className="text-slate-600" />
              </div>
              <p className="text-slate-500 text-sm">
                {filter === 'all'
                  ? 'No drafts yet. Generate messages from your pipeline!'
                  : `No ${filter} drafts.`}
              </p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {filteredDrafts.map((draft, i) => {
                const style = STATUS_STYLES[draft.status || 'pending'] || STATUS_STYLES.pending;
                const isExpanded = expandedId === draft.id;
                const isEmail = draft.subject; // If it has a subject, it's an email draft

                return (
                  <FadeUp key={draft.id} delay={0.03 * (i % 10)}>
                    <motion.div
                      layout
                      className="group bg-[#12121a] border border-white/5 rounded-xl hover:border-white/10 transition-all overflow-hidden"
                    >
                      {/* Draft Header */}
                      <div
                        onClick={() => setExpandedId(isExpanded ? null : draft.id)}
                        className="flex items-center gap-4 p-5 cursor-pointer hover:bg-white/2 transition-colors"
                      >
                        {/* Icon */}
                        <div className={`shrink-0 w-10 h-10 rounded-xl ${style.bg} flex items-center justify-center`}>
                          {isEmail ? <Mail size={18} className={style.text} /> : <Linkedin size={18} className={style.text} />}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h4 className="text-base font-semibold text-slate-200 truncate">
                              {draft.candidate_name || `Candidate #${draft.candidate_id}`}
                            </h4>
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${style.bg} ${style.text} border-current/20`}>
                              {style.label}
                            </span>
                          </div>
                          <p className="text-sm text-slate-400 truncate mt-0.5">
                            {isEmail ? draft.subject : (draft.body?.slice(0, 80) + '...')}
                          </p>
                          <p className="text-xs text-slate-600 mt-1">
                            {draft.candidate_title} {draft.candidate_company ? `at ${draft.candidate_company}` : ''}
                          </p>
                        </div>

                        {/* Right side */}
                        <div className="flex items-center gap-3 shrink-0">
                          {draft.match_score && draft.match_score > 0 && (
                            <span className={`text-xs font-bold px-2 py-0.5 rounded border shrink-0 ${
                              draft.match_score >= 80
                                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                                : 'bg-slate-800 text-slate-500 border-slate-700'
                            }`}>
                              {draft.match_score}%
                            </span>
                          )}
                          <ChevronDown
                            size={16}
                            className={`text-slate-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          />
                        </div>
                      </div>

                      {/* Expanded Content */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="px-5 pb-5 pt-0 border-t border-white/5">
                              {/* Subject (email only) */}
                              {isEmail && (
                                <div className="mt-4 mb-3">
                                  <span className="text-[10px] text-slate-600 uppercase tracking-wider">Subject</span>
                                  <p className="text-sm text-white font-medium mt-1">{draft.subject}</p>
                                </div>
                              )}

                              {/* Body */}
                              <div className="mt-3">
                                <span className="text-[10px] text-slate-600 uppercase tracking-wider">
                                  {isEmail ? 'Body' : 'Message'}
                                </span>
                                <div className="mt-2 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap bg-white/2 rounded-xl p-4 border border-white/5 font-mono text-[13px]">
                                  {draft.body}
                                </div>
                              </div>

                              {/* Generation info */}
                              {draft.generation_params?.fingerprint && (
                                <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-600">
                                  <Sparkles size={10} />
                                  <span>Prompt v{draft.generation_params.prompt_version || '?'}</span>
                                  <span className="w-1 h-1 rounded-full bg-slate-700" />
                                  <span className="font-mono">{draft.generation_params.fingerprint.slice(0, 8)}</span>
                                </div>
                              )}

                              {/* Actions */}
                              <div className="mt-4 flex items-center gap-2">
                                <Link
                                  href={`/candidates/${draft.candidate_id}`}
                                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-slate-300 hover:text-white transition-all"
                                >
                                  <ExternalLink size={14} />
                                  View Candidate
                                </Link>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigator.clipboard.writeText(draft.body || '');
                                    successToast('Draft copied to clipboard');
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-slate-300 hover:text-white transition-all"
                                >
                                  <FileText size={14} />
                                  Copy
                                </button>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  </FadeUp>
                );
              })}
            </AnimatePresence>
          )}
        </div>
      </div>
    </main>
  );
};

export default DraftsPage;
