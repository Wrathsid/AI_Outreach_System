'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import NextImage from 'next/image';
import { motion } from 'framer-motion';
import { ArrowLeft, Mail, MoreHorizontal, Search, RefreshCw, User } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { BlurIn, StaggerContainer, StaggerItem } from '@/components/Animations';

const CandidatesPage = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const loadCandidates = React.useCallback(async () => {
    setLoading(true);
    const data = await api.getCandidates();
    setCandidates(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    const init = async () => {
      await loadCandidates();
    };
    init();
  }, [loadCandidates]);

  const filteredCandidates = candidates.filter(c => 
    c.name.toLowerCase().includes(filter.toLowerCase()) || 
    c.company?.toLowerCase().includes(filter.toLowerCase()) ||
    c.title?.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <main className="flex-1 h-full overflow-y-auto p-4 md:p-8 relative">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
                <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft size={20} />
                </Link>
                <BlurIn>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Pipeline</h1>
                </BlurIn>
            </div>
            <p className="text-slate-400 ml-10">Manage and reach out to your discovered leads.</p>
          </div>
          
          <div className="flex items-center gap-3">
             <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                <input 
                    type="text" 
                    placeholder="Search pipeline..." 
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-primary/50 w-64 transition-all"
                />
             </div>
             <button 
                onClick={() => loadCandidates()}
                className="p-2 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                title="Refresh"
             >
                <RefreshCw size={20} />
             </button>
          </div>
        </header>

        {/* Content */}
        {loading ? (
             <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
             </div>
        ) : filteredCandidates.length > 0 ? (
            <StaggerContainer className="grid grid-cols-1 gap-3">
                {filteredCandidates.map((candidate) => (
                    <StaggerItem key={candidate.id}>
                        <Link href={`/candidates/${candidate.id}`}>
                            <motion.div 
                                layoutId={`candidate-${candidate.id}`}
                                className="group relative glass-panel p-4 rounded-xl border border-white/5 hover:border-primary/30 transition-all flex flex-col md:flex-row items-start md:items-center gap-4 cursor-pointer hover:bg-white/2"
                            >
                                {/* Status Indicator */}
                                <div className={`absolute left-0 top-4 bottom-4 w-1 rounded-r-full ${
                                    candidate.status === 'contacted' ? 'bg-blue-500' : 
                                    candidate.status === 'replied' ? 'bg-green-500' : 'bg-slate-700'
                                }`} />

                                <div className="ml-3 w-12 h-12 rounded-full bg-linear-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white font-bold border border-white/10 shrink-0">
                                    {candidate.avatar_url ? (
                                        <NextImage src={candidate.avatar_url} alt={candidate.name} width={48} height={48} className="w-full h-full rounded-full object-cover" unoptimized />
                                    ) : (
                                        candidate.name.charAt(0)
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-white font-medium truncate">{candidate.name}</h3>
                                        {candidate.match_score >= 80 && (
                                            <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-[10px] font-bold border border-green-500/20">
                                                {candidate.match_score}% Match
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-slate-400 text-sm truncate flex items-center gap-1.5">
                                        {candidate.title} <span className="text-slate-700">•</span> {candidate.company}
                                    </p>
                                </div>

                                <div className="flex flex-wrap gap-2 md:gap-6 items-center w-full md:w-auto mt-2 md:mt-0">
                                    {candidate.email && (
                                        <div className="flex items-center gap-1.5 text-slate-400 text-sm bg-white/5 px-3 py-1.5 rounded-lg">
                                            <Mail size={14} />
                                            <span className="truncate max-w-[150px]">{candidate.email}</span>
                                        </div>
                                    )}
                                    
                                    <div className="flex items-center gap-2 ml-auto">
                                        <div className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                                            candidate.status === 'new' ? 'bg-blue-500/10 text-blue-400' :
                                            candidate.status === 'replied' ? 'bg-emerald-500/10 text-emerald-400' :
                                            'bg-slate-500/10 text-slate-400'
                                        }`}>
                                            {candidate.status}
                                        </div>
                                        <MoreHorizontal size={20} className="text-slate-500 group-hover:text-white transition-colors" />
                                    </div>
                                </div>
                            </motion.div>
                        </Link>
                    </StaggerItem>
                ))}
            </StaggerContainer>
        ) : (
            <div className="text-center py-20">
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                    <User size={32} className="text-slate-600" />
                </div>
                <h3 className="text-white text-lg font-medium mb-2">No candidates found</h3>
                <p className="text-slate-500 max-w-md mx-auto mb-6">Your pipeline is empty. Start scanning to find new leads.</p>
                <Link href="/search">
                    <button className="px-6 py-2 bg-primary hover:bg-blue-600 text-white rounded-xl font-medium transition-colors">
                        Scan for Leads
                    </button>
                </Link>
            </div>
        )}
      </div>
    </main>
  );
};

export default CandidatesPage;
