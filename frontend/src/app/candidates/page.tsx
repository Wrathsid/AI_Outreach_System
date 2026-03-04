'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import NextImage from 'next/image';
import { ArrowLeft, RefreshCw, Trash2, Mail, ExternalLink, ChevronDown, Clock } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { cleanDisplayName, getNameInitial } from '@/lib/displayUtils';
import { useToast } from '@/context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { PipelineSkeleton } from '@/components/SkeletonLoaders';
import { useRef } from 'react';

const STATUS_OPTIONS = ['new', 'contacted', 'replied', 'snoozed'] as const;

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  new: { bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-400', label: 'New' },
  contacted: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400', label: 'Contacted' },
  replied: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400', label: 'Replied' },
  snoozed: { bg: 'bg-slate-500/10', text: 'text-slate-400', dot: 'bg-slate-400', label: 'Snoozed' },
};

// --- Status Badge with Dropdown ---
const StatusBadge = ({ candidate, onStatusChange }: { candidate: Candidate; onStatusChange: (id: number, status: string) => void }) => {
  const [open, setOpen] = useState(false);
  const status = candidate.status || 'new';
  const style = STATUS_STYLES[status] || STATUS_STYLES.new;

  return (
    <div className="relative">
      <button
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); setOpen(!open); }}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${style.bg} ${style.text} border border-white/5 hover:border-white/10 transition-all`}
      >
        {status === 'snoozed' ? <Clock size={12} /> : <div className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />}
        {style.label}
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setOpen(false); }} />
            <motion.div
              initial={{ opacity: 0, y: -4, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -4, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-1 z-50 bg-[#1a1a2e] border border-white/10 rounded-xl shadow-2xl overflow-hidden min-w-[130px]"
            >
              {STATUS_OPTIONS.map((opt) => {
                const optStyle = STATUS_STYLES[opt];
                return (
                  <button
                    key={opt}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onStatusChange(candidate.id, opt);
                      setOpen(false);
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-white/5 transition-colors ${status === opt ? 'bg-white/5' : ''}`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full ${optStyle.dot}`} />
                    <span className={optStyle.text}>{optStyle.label}</span>
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- Candidate Row ---
const CandidateRow = React.memo(({ candidate, onStatusChange }: { candidate: Candidate; onStatusChange: (id: number, status: string) => void }) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);
  const rowRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!rowRef.current) return;
    const rect = rowRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <Link href={`/candidates/${candidate.id}`}>
      <motion.div
        layout
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        ref={rowRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setOpacity(1)}
        onMouseLeave={() => setOpacity(0)}
        className="group flex items-center gap-5 p-5 rounded-xl border border-white/5 bg-[#12121a] hover:bg-[#16162a] hover:border-primary/20 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200 cursor-pointer relative"
      >
        {/* Spotlight Effect */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-xl">
          <div
            className="absolute -inset-px opacity-0 transition duration-300"
            style={{
              opacity,
              background: `radial-gradient(400px circle at ${position.x}px ${position.y}px, rgba(255,255,255,.05), transparent 40%)`,
            }}
          />
        </div>

        {/* Avatar */}
        <div className="relative shrink-0">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-white font-bold text-base border border-white/10 overflow-hidden shadow-inner">
            {candidate.avatar_url ? (
              <NextImage src={candidate.avatar_url} alt={cleanDisplayName(candidate.name)} width={44} height={44} className="w-full h-full object-cover" />
            ) : (
              getNameInitial(candidate.name)
            )}
          </div>
          {candidate.match_score > 80 && (
            <div className="absolute -bottom-0.5 -right-0.5 bg-[#0f0f12] p-0.5 rounded-full">
              <div className="w-3.5 h-3.5 rounded-full bg-green-500 flex items-center justify-center text-[7px] text-black font-bold">★</div>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-base font-semibold text-slate-200 truncate group-hover:text-white transition-colors">
              {cleanDisplayName(candidate.name)}
            </h4>
            {candidate.match_score > 0 && (
              <span 
                className={`text-xs font-bold px-2 py-0.5 rounded border shrink-0 cursor-help ${
                  candidate.match_score >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-slate-800 text-slate-500 border-slate-700'
                }`}
                title="Based on skills overlap, role alignment, and activity signals"
              >
                {candidate.match_score}%
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 truncate mt-0.5">
            {candidate.title || 'No Title'} {candidate.company ? `· ${candidate.company}` : ''}
          </p>
        </div>

        {/* Email indicator */}
        <div className="hidden sm:flex items-center gap-2 shrink-0">
          {candidate.email ? (
            <div className="flex items-center gap-1.5 text-sm text-emerald-400/70 bg-emerald-500/10 px-2.5 py-1.5 rounded-lg border border-emerald-500/10">
              <Mail size={12} />
              <span className="hidden md:inline">Email Found</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-sm text-slate-500 bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/5">
              <Mail size={12} />
              <span className="hidden md:inline">No Email</span>
            </div>
          )}
        </div>

        {/* Status — onClick stops bubbling to prevent Link navigation */}
        <div className="shrink-0" onClick={(e) => { e.stopPropagation(); }}>
          <StatusBadge candidate={candidate} onStatusChange={onStatusChange} />
        </div>

        {/* Arrow */}
        <ExternalLink size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors shrink-0 rotate-0" />
      </motion.div>
    </Link>
  );
});
CandidateRow.displayName = 'CandidateRow';


// --- Filter Tabs ---
const FilterTabs = ({ active, counts, onChange }: { active: string; counts: Record<string, number>; onChange: (v: string) => void }) => (
  <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/5">
    {[{ key: 'all', label: 'All' }, ...STATUS_OPTIONS.map(s => ({ key: s, label: STATUS_STYLES[s].label }))].map(({ key, label }) => (
      <button
        key={key}
        onClick={() => onChange(key)}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
          active === key 
            ? 'bg-white/10 text-white shadow-sm' 
            : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
        }`}
      >
        {label}
        <span className="ml-1.5 text-xs opacity-60">
          {key === 'all' ? Object.values(counts).reduce((a, b) => a + b, 0) : (counts[key] || 0)}
        </span>
      </button>
    ))}
  </div>
);


// --- Main Page ---
const CandidatesPage = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { success: successToast } = useToast();

  const loadCandidates = React.useCallback(async () => {
    try {
      const data = await api.getCandidates();
      setCandidates(data);
    } catch (error) {
      console.error("Failed to load candidates", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDeleteAll = async () => {
    if (!window.confirm('Are you sure you want to DELETE ALL candidates? This action cannot be undone.')) return;
    setLoading(true);
    const success = await api.deleteAllCandidates();
    if (success) {
      setCandidates([]);
      successToast('All candidates deleted');
    }
    setLoading(false);
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    // Optimistic update
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
    try {
      await api.updateCandidateStatus(id, newStatus);
      successToast(`Moved to ${STATUS_STYLES[newStatus]?.label || newStatus}`);
    } catch {
      loadCandidates(); // Revert on failure
    }
  };

  useEffect(() => {
    let isMounted = true;
    api.getCandidates().then(data => {
      if (isMounted) {
        setCandidates(data);
        setLoading(false);
      }
    });
    return () => { isMounted = false; };
  }, []);

  // Count by status
  const counts = React.useMemo(() => {
    const c: Record<string, number> = { new: 0, contacted: 0, replied: 0, snoozed: 0 };
    candidates.forEach(cand => { c[cand.status || 'new'] = (c[cand.status || 'new'] || 0) + 1; });
    return c;
  }, [candidates]);

  // Filter + sort
  const filteredCandidates = React.useMemo(() => {
    const list = filter === 'all' ? candidates : candidates.filter(c => (c.status || 'new') === filter);
    return [...list].sort((a, b) => b.id - a.id); // Sort by newest first
  }, [candidates, filter]);

  return (
    <main className="flex-1 h-full overflow-y-auto overflow-x-hidden flex flex-col relative w-full bg-[#0a0a0f]">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/5 blur-[120px] animate-ambient-drift" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/5 blur-[100px] animate-ambient-drift-slow" />
      </div>

      {/* Header */}
      <header className="px-6 md:px-8 py-5 flex justify-between items-center border-b border-white/5 bg-[#0f0f12]/50 backdrop-blur-md z-10 shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Pipeline
              <span className="text-slate-500 font-normal text-base">/ {candidates.length} Leads</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDeleteAll}
            className="p-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium mr-2"
            title="Delete All Candidates"
          >
            <Trash2 size={16} />
            <span className="hidden sm:inline">Delete All</span>
          </button>
          <button
            onClick={loadCandidates}
            className={`p-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      {/* Filter Bar */}
      <div className="px-6 md:px-8 py-4 z-10 shrink-0">
        <FilterTabs active={filter} counts={counts} onChange={setFilter} />
      </div>

      {/* Candidate List */}
      <div className="flex-1 px-6 md:px-8 pb-8 z-10">
        <div className="max-w-[900px] mx-auto space-y-2">
          {loading ? (
            <PipelineSkeleton />
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                <Mail size={24} className="text-slate-600" />
              </div>
              <p className="text-slate-500 text-sm">
                {filter === 'all' ? 'No candidates yet. Start a search to find leads!' : `No ${STATUS_STYLES[filter]?.label.toLowerCase()} candidates.`}
              </p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {filteredCandidates.map(candidate => (
                <CandidateRow key={candidate.id} candidate={candidate} onStatusChange={handleStatusChange} />
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>
    </main>
  );
};

export default CandidatesPage;
