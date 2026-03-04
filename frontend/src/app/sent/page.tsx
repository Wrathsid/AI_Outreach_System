'use client';

import React, { useState, useEffect } from 'react';
import { Mail, Check, Clock, ArrowRight } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { FadeUp } from '@/components/Animations';
import { PipelineSkeleton } from '@/components/SkeletonLoaders';



const SentPage = () => {
    const router = useRouter();
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'replied' | 'no-reply' | 'needs-followup'>('all');



    useEffect(() => {
        let isMounted = true;
        api.getSentCandidates().then(data => {
            if (isMounted) {
                setCandidates(data);
                setLoading(false);
            }
        });
        return () => { isMounted = false; };
    }, []);

    const daysSince = (dateStr?: string) => {
        if (!dateStr) return 0;
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24));
    };

    const filteredCandidates = candidates.filter(c => {
        if (filter === 'replied') return c.reply_received;
        if (filter === 'no-reply') return !c.reply_received;
        if (filter === 'needs-followup') return !c.reply_received && daysSince(c.sent_at) >= 5;
        return true;
    });

    const stats = {
        total: candidates.length,
        replied: candidates.filter(c => c.reply_received).length,
        noReply: candidates.filter(c => !c.reply_received).length,
        needsFollowup: candidates.filter(c => !c.reply_received && daysSince(c.sent_at) >= 5).length,
    };

    return (
        <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
            {/* Background Ambience */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-green-600/10 blur-[120px]"></div>
                <div className="absolute bottom-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-blue-600/10 blur-[100px]"></div>
            </div>

            <div className="z-10 w-full max-w-4xl mx-auto">
                {/* Header */}
                <FadeUp className="mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                        <Mail size={32} className="text-green-500" />
                        Sent Messages
                    </h1>
                    <p className="text-slate-400">Track your outreach and responses</p>
                </FadeUp>

                {/* Stats Cards */}
                <FadeUp delay={0.1} className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                        <p className="text-slate-400 text-xs mb-1">Total Sent</p>
                        <p className="text-2xl font-bold text-white">{stats.total}</p>
                    </div>
                    <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
                        <p className="text-green-400 text-xs mb-1">Replied</p>
                        <p className="text-2xl font-bold text-green-500">{stats.replied}</p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                        <p className="text-slate-400 text-xs mb-1">No Reply</p>
                        <p className="text-2xl font-bold text-white">{stats.noReply}</p>
                    </div>
                    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
                        <p className="text-yellow-400 text-xs mb-1">Needs Follow-up</p>
                        <p className="text-2xl font-bold text-yellow-500">{stats.needsFollowup}</p>
                    </div>
                </FadeUp>

                {/* Filter Tabs */}
                <FadeUp delay={0.2} className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {[
                        { key: 'all' as const, label: 'All', count: stats.total },
                        { key: 'replied' as const, label: 'Replied', count: stats.replied },
                        { key: 'no-reply' as const, label: 'No Reply', count: stats.noReply },
                        { key: 'needs-followup' as const, label: 'Needs Follow-up', count: stats.needsFollowup },
                    ].map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setFilter(tab.key)}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                                filter === tab.key
                                    ? 'bg-white text-black'
                                    : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
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
                        <Mail size={48} className="mx-auto mb-4 text-slate-600" />
                        <p className="text-slate-400 text-lg mb-2">
                            {filter === 'all' 
                                ? 'No messages sent yet'
                                : filter === 'replied'
                                ? 'No replies yet'
                                : filter === 'needs-followup'
                                ? 'No follow-ups needed'
                                : 'No unreplied messages'
                            }
                        </p>
                        <p className="text-slate-600 text-sm">
                            {filter === 'all' && 'Start reaching out to candidates from your pipeline'}
                        </p>
                    </FadeUp>
                )}

                {/* Candidate List */}
                {!loading && filteredCandidates.length > 0 && (
                    <div className="space-y-3">
                        {filteredCandidates.map((c, i) => {
                            const days = daysSince(c.sent_at);
                            const needsFollowup = !c.reply_received && days >= 5;

                            return (
                                <FadeUp key={c.id} delay={0.02 * i}>
                                    <div
                                        onClick={() => router.push(`/candidates/${c.id}`)}
                                        className="group bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl p-5 transition-all cursor-pointer"
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            {/* Left: Info */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-lg font-medium text-white truncate">
                                                        {c.name}
                                                    </h3>
                                                    
                                                    {/* Status Badge */}
                                                    {c.reply_received ? (
                                                        <span className="flex items-center gap-1.5 text-xs bg-green-500/20 text-green-400 px-2.5 py-1 rounded-full border border-green-500/30">
                                                            <Check size={12} strokeWidth={3} />
                                                            Replied
                                                        </span>
                                                    ) : needsFollowup ? (
                                                        <span className="flex items-center gap-1.5 text-xs bg-yellow-500/20 text-yellow-400 px-2.5 py-1 rounded-full border border-yellow-500/30">
                                                            <Clock size={12} />
                                                            Follow-up
                                                        </span>
                                                    ) : (
                                                        <span className="flex items-center gap-1.5 text-xs bg-slate-500/20 text-slate-400 px-2.5 py-1 rounded-full border border-slate-500/30">
                                                            <Clock size={12} />
                                                            Pending
                                                        </span>
                                                    )}
                                                </div>

                                                <p className="text-sm text-slate-400 mb-1">
                                                    {c.title} at {c.company}
                                                </p>

                                                <div className="flex items-center gap-3 text-xs text-slate-500">
                                                    <span>
                                                        {c.reply_received
                                                            ? `Replied ${daysSince(c.reply_at)} days ago`
                                                            : `Sent ${days} day${days !== 1 ? 's' : ''} ago`
                                                        }
                                                    </span>
                                                    {c.email && (
                                                        <>
                                                            <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
                                                            <span className="font-mono">{c.email}</span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Right: Action */}
                                            <div className="shrink-0 flex items-center gap-2">
                                                {needsFollowup && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            router.push(`/candidates/${c.id}`);
                                                        }}
                                                        className="bg-yellow-500 hover:bg-yellow-400 text-black px-4 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2"
                                                    >
                                                        Send Follow-up
                                                        <ArrowRight size={14} />
                                                    </button>
                                                )}
                                                
                                                <ArrowRight 
                                                    size={20} 
                                                    className="text-slate-600 group-hover:text-white group-hover:translate-x-1 transition-all" 
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </FadeUp>
                            );
                        })}
                    </div>
                )}
            </div>
        </main>
    );
};

export default SentPage;
