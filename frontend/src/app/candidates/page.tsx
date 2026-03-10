'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import NextImage from 'next/image';
import { RefreshCw, Trash2, Mail, ExternalLink, ChevronDown, Clock, Users } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { cleanDisplayName, getNameInitial } from '@/lib/displayUtils';
import { useToast } from '@/context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { PipelineSkeleton } from '@/components/SkeletonLoaders';
import { FadeUp } from '@/components/Animations';
import { useRef } from 'react';

const STATUS_OPTIONS = ['new', 'contacted', 'snoozed'] as const;

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  new: { bg: 'bg-blue-500/10', text: 'text-blue-400', dot: 'bg-blue-400', label: 'Non-contacted' },
  contacted: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400', label: 'Contacted' },

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
const CandidateRow = React.memo(({ candidate, onStatusChange, index = 0 }: { candidate: Candidate; onStatusChange: (id: number, status: string) => void; index?: number }) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);
  const rowRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!rowRef.current) return;
    const rect = rowRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <Link href={`/candidates/${candidate.id}`} className="block relative" style={{ zIndex: 1000 - index }}>
      <motion.div
        layout
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        ref={rowRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setOpacity(1)}
        onMouseLeave={() => setOpacity(0)}
        className="group flex items-center gap-5 p-5 rounded-xl border border-white/5 bg-white/2 hover:glass-panel hover:-translate-y-0.5 transition-all duration-300 cursor-pointer relative"
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
          <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-white font-bold text-base border border-white/10 overflow-hidden shadow-inner ring-1 ring-white/5 group-hover:ring-primary/30 transition-all duration-300">
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

  const handleStatusChange = React.useCallback(async (id: number, newStatus: string) => {
    // Optimistic update
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
    try {
      await api.updateCandidateStatus(id, newStatus);
      successToast(`Moved to ${STATUS_STYLES[newStatus]?.label || newStatus}`);
    } catch {
      loadCandidates(); // Revert on failure
    }
  }, [successToast, loadCandidates]);

  useEffect(() => {
    let isMounted = true;
    api.getCandidates().then(data => {
      if (isMounted) {
        setCandidates(data);
        setLoading(false);
      }
    });

    const refreshData = () => {
      api.getCandidates().then(data => {
        if (isMounted) setCandidates(data);
      });
    };

    window.addEventListener('popstate', refreshData);
    window.addEventListener('candidates_updated', refreshData);
    
    return () => { 
      isMounted = false; 
      window.removeEventListener('popstate', refreshData);
      window.removeEventListener('candidates_updated', refreshData);
    };
  }, []);

  // Count by status
  const counts = React.useMemo(() => {
    const c: Record<string, number> = { new: 0, contacted: 0, snoozed: 0 };
    candidates.forEach(cand => { c[cand.status || 'new'] = (c[cand.status || 'new'] || 0) + 1; });
    return c;
  }, [candidates]);

  const totalCount = candidates.length;

  // Filter + sort
  const filteredCandidates = React.useMemo(() => {
    const list = filter === 'all' ? candidates : candidates.filter(c => (c.status || 'new') === filter);
    return [...list].sort((a, b) => b.id - a.id); // Sort by newest first
  }, [candidates, filter]);

  const statCards = [
    { label: 'Total Leads', value: totalCount, style: 'glass-panel', labelColor: 'text-slate-400', valueColor: 'text-white' },
    { label: 'Non-contacted', value: counts.new, style: 'glass-panel border-blue-500/20 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05),0_0_20px_-5px_rgba(59,130,246,0.15)]', labelColor: 'text-blue-400', valueColor: 'text-blue-500' },
    { label: 'Contacted', value: counts.contacted, style: 'glass-panel border-amber-500/20 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05),0_0_20px_-5px_rgba(245,158,11,0.15)]', labelColor: 'text-amber-400', valueColor: 'text-amber-500' },
  ];

  const filterTabs = [
    { key: 'all', label: 'All', count: totalCount },
    { key: 'new', label: 'Non-contacted', count: counts.new },
    { key: 'contacted', label: 'Contacted', count: counts.contacted },

    { key: 'snoozed', label: 'Snoozed', count: counts.snoozed },
  ];

  return (
    <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-blue-600/10 blur-[120px] animate-ambient-drift"></div>
        <div className="absolute bottom-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-purple-600/10 blur-[100px] animate-ambient-drift-slow"></div>
      </div>

      <div className="z-10 w-full max-w-[1600px] mx-auto">
        {/* Header */}
        <FadeUp className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                <Users size={32} className="text-blue-500" />
                Pipeline
              </h1>
              <p className="text-slate-400">Track and manage your candidate leads</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDeleteAll}
                className="p-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium"
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
          </div>
        </FadeUp>

        {/* Stats Cards */}
        <FadeUp delay={0.1} className="grid grid-cols-3 gap-4 mb-6">
          {statCards.map((card) => (
            <div key={card.label} className={`${card.style} rounded-xl p-4 hover-lift transition-transform`}>
              <p className={`${card.labelColor} text-xs mb-1 font-medium tracking-wide uppercase`}>{card.label}</p>
              <p className={`text-2xl font-bold ${card.valueColor}`}>{card.value}</p>
            </div>
          ))}
        </FadeUp>

        {/* Filter Tabs */}
        <FadeUp delay={0.2} className="flex gap-2 mb-6 overflow-x-auto pb-2 custom-scrollbar">
          {filterTabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-4 py-2 rounded-full text-sm transition-all whitespace-nowrap border ${
                filter === tab.key
                  ? 'bg-blue-500/10 text-blue-400 border-blue-500/30 shadow-glow font-medium'
                  : 'bg-white/5 text-white/50 border-white/5 hover:bg-white/10 hover:text-white/90 hover:border-white/20'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </FadeUp>

        {/* Loading State */}
        {loading && (
          <div className="py-2">
            <PipelineSkeleton />
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredCandidates.length === 0 && (
          <FadeUp className="text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 animate-float">
              <Users size={28} className="text-slate-600" />
            </div>
            <p className="text-slate-400 text-lg mb-2">
              {filter === 'all'
                ? 'No candidates yet'
                : `No ${STATUS_STYLES[filter]?.label.toLowerCase() || filter} candidates`
              }
            </p>
            <p className="text-slate-600 text-sm">
              {filter === 'all' && 'Start a search to find leads and build your pipeline'}
            </p>
          </FadeUp>
        )}

        {/* Candidate List */}
        {!loading && filteredCandidates.length > 0 && (
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {filteredCandidates.map((candidate, index) => (
                <CandidateRow key={candidate.id} candidate={candidate} onStatusChange={handleStatusChange} index={index} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </main>
  );
};

export default CandidatesPage;
