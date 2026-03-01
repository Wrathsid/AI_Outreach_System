'use client';

import React, { useState, useEffect } from 'react';
import { Search, Loader2, Mail, Check, Github, Linkedin, Sparkles, Building2, Briefcase, User } from 'lucide-react';
import { API_BASE, api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { FadeUp } from '@/components/Animations';
import { useToast } from '@/context/ToastContext';
import { createClient } from '@/lib/supabase';

// Reuse ScanResult type or similar
interface ScanResult {
    name: string;
    title: string;
    company: string;
    email?: string;
    generated_email?: string;  // AI-generated email guess
    email_confidence?: number;  // Confidence score 0-100
    linkedin_url: string;
    summary?: string;
    is_hr?: boolean;
    hr_score?: number;
    resonance_score?: number;
    result_type?: 'job_posting' | 'person';  // Classification from backend
}



const PLACEHOLDERS = [
    "Search roles like 'Frontend Engineer'...",
    "Search roles like 'Startup CTO'...",
    "Search roles like 'DevOps Manager'...",
    "Search roles like 'Technical Recruiter'...",
    "Search roles like 'Product Owner'..."
];

const EXAMPLE_CHIPS = [
    "Web Developer",
    "Product Manager",
    "DevOps",
    "AI Engineer"
];

// Email Status Badge Component (UX Improvement)
const EmailBadge = ({ confidence }: { confidence?: number }) => {
    if (!confidence) return <span className="text-[10px] text-slate-600">❓ Unknown</span>;
    
    if (confidence >= 80) {
        return <span className="text-[10px] text-green-500 flex items-center gap-0.5">✅ Verified</span>;
    } else if (confidence >= 50) {
        return <span className="text-[10px] text-yellow-500 flex items-center gap-0.5">⚠️ Risky</span>;
    } else {
        return <span className="text-[10px] text-red-500 flex items-center gap-0.5">❌ Invalid</span>;
    }
};

const SearchPage = () => {
    const router = useRouter(); // Auto-redirect after adding leads
    const [role, setRole] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [results, setResults] = useState<ScanResult[]>([]);
    const [isAdding, setIsAdding] = useState(false);
    
    // Rotating Placeholder Logic
    const [placeholderIndex, setPlaceholderIndex] = useState(0);
    useEffect(() => {
        const interval = setInterval(() => {
            setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDERS.length);
        }, 3000);
        return () => clearInterval(interval);
    }, []);


    const [isSelectMode, setIsSelectMode] = useState(false);
    const [selectedEmails, setSelectedEmails] = useState<Set<string>>(new Set());
    const { success } = useToast();

    // Toggle selection of a single candidate
    const toggleSelection = (email: string) => {
        const newSelected = new Set(selectedEmails);
        if (newSelected.has(email)) {
            newSelected.delete(email);
        } else {
            newSelected.add(email);
        }
        setSelectedEmails(newSelected);
    };

    // Toggle select all
    const toggleSelectAll = () => {
        if (selectedEmails.size === results.length && results.length > 0) {
            setSelectedEmails(new Set());
        } else {
            const allEmails = new Set(results.map(r => r.email || r.linkedin_url)); // Use fallback if email missing
            setSelectedEmails(allEmails);
        }
    };
    
    // Derived state for Select All checkbox
    const isAllSelected = results.length > 0 && selectedEmails.size === results.length;
    
    // Auto-enable select mode if items are selected
    useEffect(() => {
        if (selectedEmails.size > 0 && !isSelectMode) {
            setIsSelectMode(true);
        }
    }, [selectedEmails, isSelectMode]);
    
    const [statusMessage, setStatusMessage] = useState('');



    // Polling logic for Temporal workflow
    const pollTemporalStatus = async (jobId: string, headers: Headers) => {
        try {
            const res = await fetch(`${API_BASE}/discover/temporal-discover/${jobId}`, { headers });
            const data = await res.json();
            
            if (data.status === "completed") {
                setResults(data.results || []);
                setStatusMessage('Scan complete.');
                setIsScanning(false);
                setTimeout(() => setStatusMessage(''), 3000);
            } else if (data.status === "failed") {
                setStatusMessage('Scan failed.');
                setIsScanning(false);
            } else {
                setStatusMessage('Temporal Workflow running... polling status');
                setTimeout(() => pollTemporalStatus(jobId, headers), 3000); // 3-second poll
            }
        } catch (e) {
            console.error(e);
            setStatusMessage('Error polling status.');
            setIsScanning(false);
        }
    };

    // Trigger Temporal Scan
    const handleScan = async (roleOverride?: string) => {
        const searchRole = roleOverride || role;
        if (!searchRole) return;
        setIsScanning(true);
        setStatusMessage('Starting durable Temporal scan...');
        setResults([]);
        
        try {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const headers = new Headers();
            if (session?.access_token) {
                headers.set('Authorization', `Bearer ${session.access_token}`);
            }

            // Fire off the background workflow
            const response = await fetch(`${API_BASE}/discover/temporal-discover?role=${encodeURIComponent(searchRole)}&limit=15`, { 
                method: 'POST',
                headers 
            });
            const data = await response.json();
            
            if (data.status === 'running' && data.job_id) {
                // Begin robust polling
                pollTemporalStatus(data.job_id, headers);
            } else {
                throw new Error("Failed to start workflow");
            }
        } catch (e) {
            console.error(e);
            setStatusMessage('Scan failed to start.');
            setIsScanning(false);
        }
    };

    return (
        <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
            {/* Background Ambience */}
            <div className="fixed inset-0 pointer-events-none z-0">
                 <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-blue-600/10 blur-[120px]"></div>
                 <div className="absolute bottom-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-purple-600/10 blur-[100px]"></div>
            </div>

            <div className={`z-10 w-full max-w-2xl mx-auto flex flex-col items-center transition-all duration-500 ${results.length > 0 ? 'mt-10 mb-8' : 'my-auto mt-[15vh]'}`}>
                
                {/* Header Pills Removed for Simplicity */}
                <div className="h-20"></div> {/* Spacer */}

                {/* Zero-State Intent (Only show when empty) */}
                {results.length === 0 && !isScanning && (
                    <FadeUp delay={0.2} className="mb-8 text-center">
                        <h2 className="text-2xl font-medium text-white mb-2">
                           Find hiring managers, recruiters, or teams by role
                        </h2>
                        <p className="text-slate-400 text-sm">
                            Scans LinkedIn Hiring posts
                        </p>
                    </FadeUp>
                )}

                {/* Search Input */}
                <FadeUp delay={0.3} className="w-full relative group z-50 pointer-events-none">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    <div className="relative z-20 pointer-events-auto">
                        <div className="relative flex items-center bg-black/40 border border-white/10 rounded-full p-2 pl-6 backdrop-blur-xl shadow-2xl ring-1 ring-white/5 focus-within:ring-primary/50 focus-within:shadow-glow transition-all duration-300">
                            <Search className={`text-slate-500 transition-colors duration-300 ${role ? 'text-primary' : ''}`} size={24} />
                            <input 
                                type="text" 
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && role) {
                                        e.preventDefault();
                                        handleScan();
                                    }
                                }}
                                className="flex-1 bg-transparent border-none outline-none text-white px-4 py-4 text-lg placeholder-slate-500"
                                placeholder={PLACEHOLDERS[placeholderIndex]}
                                spellCheck={false}
                                autoCorrect="off"
                                autoComplete="off"
                                autoCapitalize="off"
                            />
                            
                            {role && (
                                <div className="flex items-center gap-2 mr-2 animate-in fade-in slide-in-from-right-4 duration-300">

                                    {(role.length > 2) && (
                                        <button 
                                            onClick={() => handleScan()}
                                            disabled={isScanning || !role}
                                            className="bg-primary hover:bg-blue-600 text-white rounded-full px-5 py-2 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 flex items-center gap-2"
                                        >
                                            {isScanning ? (
                                                <Loader2 className="animate-spin" size={16} />
                                            ) : (
                                                <>
                                                    <span>Scan</span>
                                                    <Sparkles size={14} className="opacity-70" />
                                                </>
                                            )}
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                        
                        {/* Status Message */}
                        {isScanning && statusMessage && (
                            <FadeUp delay={0.1} className="mt-4 text-center">
                                <p className="text-sm text-slate-400 font-mono animate-pulse">{statusMessage}</p>
                            </FadeUp>
                        )}
                    </div>


                    {/* Example Chips (Zero State) */}
                    {!role && results.length === 0 && !isScanning && (
                        <div className="flex flex-wrap items-center justify-center gap-3 mt-6 animate-in fade-in slide-in-from-top-2 duration-700 delay-150 pointer-events-auto">
                            <span className="text-slate-600 text-sm mr-1">Try:</span>
                            {EXAMPLE_CHIPS.map((chip, i) => (
                                <button
                                    key={i}
                                    onClick={() => { setRole(chip); setTimeout(() => handleScan(chip), 50); }}
                                    className="text-sm text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-1 rounded-full transition-colors border border-white/5 hover:border-white/20"
                                >
                                    {chip}
                                </button>
                            ))}
                        </div>
                    )}
                </FadeUp>

                {/* Real-time Results Stack */}
                {results.length > 0 ? (
                    <div className="w-full mt-8 space-y-4 pb-20 override-scroll">
                        {/* Sort info / Action Bar */}
                        <div className="flex justify-between items-center mb-2 px-2 text-[10px] text-slate-500 font-medium uppercase tracking-widest animate-in fade-in">
                            <span>
                                {results.filter(r => r.result_type !== 'job_posting').length} People
                                {results.filter(r => r.result_type === 'job_posting').length > 0 && (
                                    <> · {results.filter(r => r.result_type === 'job_posting').length} Job Postings</>
                                )}
                            </span>
                            <span className="flex items-center gap-1.5 text-primary">
                                <Sparkles size={10} />
                                sorted by resonance
                            </span>
                        </div>
                        
                        <div className="relative z-10 flex items-center justify-between px-2 mb-2 animate-in fade-in slide-in-from-bottom-2 h-10">
                             <div className="flex items-center gap-3">
                                {!isSelectMode ? (
                                    <button 
                                        onClick={() => setIsSelectMode(true)}
                                        className="text-xs font-medium text-slate-400 hover:text-white transition-colors"
                                    >
                                        Select...
                                    </button>
                                ) : (
                                    <button 
                                        onClick={toggleSelectAll}
                                        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors group animate-in slide-in-from-left-2"
                                    >
                                        <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${isAllSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-600 group-hover:border-slate-400'}`}>
                                            {isAllSelected && <Check size={10} className="text-white" strokeWidth={3} />}
                                        </div>
                                        <span>All ({results.length})</span>
                                    </button>
                                )}
                             </div>
                             
                             {selectedEmails.size > 0 && (
                                <button 
                                    onClick={async () => {
                                        setIsAdding(true);
                                        try {
                                            // 1. Filter selected results first
                                            const selectedResults = results.filter(r => {
                                                const id = r.email || r.linkedin_url;
                                                return selectedEmails.has(id);
                                            });

                                            // 2. Create candidates and generate drafts in PARALLEL
                                            const creationPromises = selectedResults.map(async (r) => {
                                                try {
                                                    const res = await api.createCandidate({
                                                        name: r.name,
                                                        title: r.title,
                                                        company: r.company,
                                                        linkedin_url: r.linkedin_url,
                                                        email: r.email,
                                                        generated_email: r.generated_email,
                                                        email_confidence: r.email_confidence,
                                                        summary: r.summary,
                                                        match_score: r.resonance_score !== undefined ? Math.round(r.resonance_score * 100) : (r.hr_score ? Math.round(r.hr_score * 100) : 50),
                                                        status: 'new'
                                                    });
                                                    
                                                    if (res?.id) {
                                                        return res.id;
                                                    }
                                                } catch (err) {
                                                    console.error(`Failed to create candidate ${r.name}`, err);
                                                    return null;
                                                }
                                                return null;
                                            });

                                            const createdIds = (await Promise.all(creationPromises)).filter(id => id !== null) as number[];
                                            
                                            // 3. Bulk pipeline update
                                            if (createdIds.length > 0) {
                                                // Fire and forget the background draft generator for all candidates
                                                api.generateDraftsBatch(createdIds, "auto").then((res) => {
                                                    if (res?.task_id) {
                                                        localStorage.setItem('active_batch_task', res.task_id);
                                                    }
                                                }).catch(console.error);
                                                
                                                await api.bulkAddToPipeline(createdIds);
                                                success(`Added ${createdIds.length} leads. AI drafts are generating in the background!`);
                                                
                                                // Remove added candidates from search results
                                                setResults(prev => prev.filter(r => {
                                                    const id = r.email || r.linkedin_url;
                                                    return !selectedEmails.has(id);
                                                }));
                                                
                                                setSelectedEmails(new Set());
                                                
                                                // Redirect to Pipeline (Dashboard)
                                                router.push('/');
                                            } else {
                                                setIsAdding(false);
                                            }
                                        } catch (e) {
                                            console.error(e);
                                            setIsAdding(false);
                                        }
                                    }}
                                    disabled={isAdding}
                                    className="bg-white text-black text-xs font-bold px-4 py-1.5 rounded-full hover:bg-slate-200 transition-colors shadow-lg shadow-white/10 animate-in zoom-in-50 disabled:opacity-70 disabled:cursor-wait flex items-center gap-2"
                                >
                                    {isAdding ? (
                                        <>
                                            <Loader2 className="animate-spin" size={12} />
                                            <span>Adding...</span>
                                        </>
                                    ) : (
                                        <span>Add to Pipeline ({selectedEmails.size})</span>
                                    )}
                                </button>
                             )}
                        </div>

                        {results.map((r, i) => {
                            const id = r.email || r.linkedin_url;
                            const isSelected = selectedEmails.has(id);
                            return (
                                <FadeUp key={i} delay={0.05 * (i % 5)}>
                                    <div 
                                        onClick={() => toggleSelection(id)}
                                        className={`group relative flex items-start gap-4 p-5 rounded-2xl border transition-all ${
                                            isSelected 
                                                ? 'bg-blue-500/5 border-blue-500/20' 
                                                : 'bg-white/5 hover:bg-white/10 border-white/5 hover:border-white/10'
                                        }`}
                                    >
                                        {/* Checkbox (Animated) */}
                                        <div className={`shrink-0 pt-1 transition-all duration-300 ${isSelectMode ? 'w-5 opacity-100' : 'w-0 opacity-0 overflow-hidden'}`}>
                                             <div 
                                                onClick={(e) => { e.stopPropagation(); toggleSelection(id); }}
                                                className={`w-5 h-5 rounded border flex items-center justify-center cursor-pointer ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-600 hover:border-slate-500'}`}
                                             >
                                                {isSelected && <Check size={12} className="text-white" strokeWidth={3} />}
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0 flex flex-col gap-2">
                                            {/* Header: Name + Metadata */}
                                            <div>
                                                <div className="flex items-baseline justify-between">
                                                    <h3 className="text-lg font-medium text-white truncate pr-4">
                                                        {r.name}
                                                    </h3>
                                                    {/* Type Badge */}
                                                    <div className="shrink-0 flex items-center gap-1.5">
                                                        {r.result_type === 'job_posting' ? (
                                                            <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded-full">
                                                                <Briefcase size={10} />
                                                                Job Posting
                                                            </span>
                                                        ) : (
                                                            <span className="flex items-center gap-1 text-[10px] font-semibold text-blue-400 bg-blue-400/10 border border-blue-400/20 px-2 py-0.5 rounded-full">
                                                                <User size={10} />
                                                                Person
                                                            </span>
                                                        )}
                                                        {/* Source Badge (Subtle) */}
                                                        <span className="text-[10px] text-slate-500 opacity-60">
                                                            {r.linkedin_url.includes('github') ? <Github size={10} /> : <Linkedin size={10} />}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="text-sm text-slate-400 truncate flex items-center gap-2">
                                                    <span className="text-slate-300">{r.title}</span>
                                                    <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                                                    <span className="flex items-center gap-1">
                                                        <Building2 size={10} className="opacity-70" />
                                                        {r.company}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Resonance Indicator (Phase 3) */}
                                            {r.resonance_score !== undefined && r.resonance_score > 0 && (
                                                <div className="flex items-center gap-2 mt-1">
                                                    <div className="flex gap-0.5">
                                                        {[1, 2, 3, 4, 5].map((i) => (
                                                            <div 
                                                                key={i} 
                                                                className={`w-1 h-3 rounded-full transition-all duration-500 ${
                                                                    (r.resonance_score! * 5) >= i 
                                                                        ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]' 
                                                                        : 'bg-white/10'
                                                                }`}
                                                            />
                                                        ))}
                                                    </div>
                                                    <span className="text-[10px] font-medium text-blue-400 uppercase tracking-wider">
                                                        {r.resonance_score > 0.8 ? 'High Signal' : r.resonance_score > 0.5 ? 'Strong Match' : 'Potentially Relevant'}
                                                    </span>
                                                </div>
                                            )}

                                            {/* Context / Intent (1 Line Max) */}
                                            {r.summary && (
                                                <p className="text-xs text-slate-500 line-clamp-1 leading-relaxed">
                                                    {r.summary.replace(/• Unknown|Unknown/g, '').trim()}
                                                </p>
                                            )}
                                        </div>

                                        {/* Actions (Vertical Alignment) */}
                                        <div className="flex flex-col items-end gap-2 shrink-0 pl-4 border-l border-white/5 ml-2 min-w-[100px]">
                                             <button 
                                                onClick={() => window.open(r.linkedin_url, '_blank')}
                                                className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors shadow-lg shadow-blue-500/10"
                                             >
                                                <Linkedin size={12} />
                                                <span>LinkedIn</span>
                                             </button>
                                             
                                             {r.email && (
                                                <>
                                                    <button 
                                                        className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg border border-slate-700/50 hover:bg-white/5 text-slate-400 hover:text-white text-xs transition-colors"
                                                        title={r.email}
                                                        onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(r.email!); success('Email copied'); }}
                                                    >
                                                        <Mail size={12} />
                                                        <span>Email</span>
                                                    </button>
                                                    {/* Email Status Badge (UX Improvement) */}
                                                    <div className="text-center -mt-1">
                                                        <EmailBadge confidence={r.email_confidence} />
                                                    </div>
                                                </>
                                             )}
                                        </div>
                                    </div>
                                </FadeUp>
                            );
                        })}
                    </div>
                ) : null}

            </div>



        </main>
    );
};

export default SearchPage;
