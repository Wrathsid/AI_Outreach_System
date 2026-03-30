'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Loader2, Mail, Check, Github, Linkedin, Sparkles, Building2 } from 'lucide-react';
import { API_BASE, api } from '@/lib/api';
import { JOB_TITLES } from '@/data/jobTitles';
import { useRouter } from 'next/navigation';
import { FadeUp } from '@/components/Animations';
import { useToast } from '@/context/ToastContext';

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
    
    // Suggestions State
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
    const [showSuggestions, setShowSuggestions] = useState(false);
    
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
    const { success, error: toastError } = useToast();

    // Ref to track auto-processed count for the current scan session
    const autoProcessedCountRef = useRef(0);

    // Toggle selection of a single candidate
    const toggleSelection = useCallback((email: string) => {
        setSelectedEmails(prev => {
            const newSelected = new Set(prev);
            if (newSelected.has(email)) {
                newSelected.delete(email);
            } else {
                newSelected.add(email);
            }
            return newSelected;
        });
    }, []);

    // Toggle select all
    const toggleSelectAll = () => {
        if (selectedEmails.size === results.length && results.length > 0) {
            setSelectedEmails(new Set());
        } else {
            const allIds = new Set(results.map((r, idx) => r.email || r.linkedin_url || `result-${idx}`));
            setSelectedEmails(allIds);
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



    // Real-time WebSocket logic for direct backend processing
    const connectDirectWebSocket = (searchRole: string, limit: number = 15) => {
        // Build WebSocket URL: strip any path suffix like /api from API_BASE
        const baseUrl = API_BASE.replace(/\/api\/?$/, '');
        const wsUrl = `${baseUrl.replace(/^http/, 'ws')}/discover/ws/discover?role=${encodeURIComponent(searchRole)}&limit=${limit}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
             setStatusMessage('Connected. Engine starting up...');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.status === "completed") {
                    // Update final results if provided
                    if (data.results && data.results.length > 0) {
                        // Avoid duplicates if we already streamed them
                        if (results.length === 0) setResults(data.results);
                    }
                    setStatusMessage('Scan complete.');
                    setIsScanning(false);
                    setTimeout(() => setStatusMessage(''), 3000);
                    ws.close();
                } else if (data.status === "failed" || data.status === "error") {
                    setStatusMessage('Scan error: ' + (data.message || 'Unknown error'));
                    setIsScanning(false);
                    ws.close();
                } else if (data.status === "lead_discovered") {
                    // Stream single lead into the UI instantly!
                    const lead = data.lead;
                    setResults(prev => [...prev, lead]);

                    // AUTO-PROCESSING Logic: Trigger background draft generation for top high-scoring leads
                    // Only process first 3 results with resonance > 0.8
                    if (autoProcessedCountRef.current < 3 && lead.resonance_score > 0.8) {
                        autoProcessedCountRef.current++;
                        
                        // 1. Silent creation
                        api.createCandidate({
                            name: lead.name || 'Unknown Candidate',
                            title: lead.title || undefined,
                            company: lead.company || undefined,
                            linkedin_url: lead.linkedin_url || undefined,
                            email: lead.email || undefined,
                            generated_email: lead.generated_email || undefined,
                            email_confidence: lead.email_confidence,
                            summary: lead.summary || undefined,
                            match_score: Math.round((lead.resonance_score || 0.5) * 100),
                            status: 'discovered', // Special background status
                            tags: [searchRole]
                        }).then(candidate => {
                            if (candidate?.id) {
                                // 2. Trigger batch generation (sequential background task)
                                api.generateDraftsBatch([candidate.id], "auto").catch(console.error);
                            }
                        }).catch(err => console.warn("Background auto-creation failed", err));
                    }
                } else if (data.status === "running") {
                    setStatusMessage(data.message || 'Scanning... streaming status');
                }
            } catch (e) {
                console.error("Message JSON parse error", e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            setStatusMessage('WebSocket connection error. Make sure the backend is running.');
            toastError('WebSocket Error! Could not connect to API.');
            setIsScanning(false);
        };
        
        ws.onclose = (event) => {
            // If it closed immediately, it might be an error not caught by onerror
            if (isScanning && event.code !== 1000) {
                 toastError(`WS Closed abruptly (Code ${event.code})`);
                 setIsScanning(false);
            }
        };
        
        return ws;
    };

    // Trigger Scan
    const handleScan = async (roleOverride?: string) => {
        const searchRole = roleOverride || role;
        if (!searchRole) return;
        
        // Reset auto-processing counter for new scan
        autoProcessedCountRef.current = 0;

        setIsScanning(true);
        setStatusMessage('Connecting to search engine...');
        setResults([]);
        setSelectedEmails(new Set());
        setIsSelectMode(false);
        
        try {
            // Directly open the websocket stream
            connectDirectWebSocket(searchRole);
        } catch (error) {
            console.warn("Scan initiation error:", error);
            setStatusMessage('Scan failed to start.');
            setIsScanning(false);
        }
    };

    const renderedResults = React.useMemo(() => {
        return results.map((r, i) => {
            const id = (r.email || r.linkedin_url || `result-${i}`) as string;
            const isSelected = selectedEmails.has(id);
            return (
                <FadeUp key={id} delay={0.05 * (i % 5)}>
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
                                        {r.name && r.name !== 'Unknown Candidate' && r.name !== 'Unknown' 
                                            ? r.name 
                                            : (r.title || 'LinkedIn Member')}
                                    </h3>
                                    {/* Source Badge (Subtle) */}
                                    <div className="shrink-0 flex items-center gap-1.5">
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
                                        {[1, 2, 3, 4, 5].map((idx) => (
                                            <div 
                                                key={idx} 
                                                className={`w-1 h-3 rounded-full transition-all duration-500 ${
                                                    (() => {
                                                        const score = r.resonance_score!;
                                                        const bars = score > 0.8 ? 5 : score > 0.5 ? 4 : score > 0.2 ? 3 : 2;
                                                        return bars >= idx;
                                                    })()
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
        });
    }, [results, selectedEmails, isSelectMode, toggleSelection, success]);

    return (
        <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
            {/* Background Ambience */}
            <div className="fixed inset-0 pointer-events-none z-0">
                 <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-blue-600/10 blur-[120px]"></div>
                 <div className="absolute bottom-[20%] right-[20%] w-[30%] h-[30%] rounded-full bg-purple-600/10 blur-[100px]"></div>
            </div>

            <div className={`z-10 w-full max-w-4xl mx-auto flex flex-col items-center transition-all duration-500 ${results.length > 0 ? 'mt-10 mb-8' : 'my-auto mt-[15vh]'}`}>
                
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
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setRole(val);
                                    if (val.length > 0) {
                                        const filtered = JOB_TITLES.filter(title => title.toLowerCase().includes(val.toLowerCase())).slice(0, 6);
                                        setSuggestions(filtered);
                                        setShowSuggestions(true);
                                        setActiveSuggestionIndex(-1);
                                    } else {
                                        setShowSuggestions(false);
                                    }
                                }}
                                onFocus={() => {
                                    if (role.length > 0 && suggestions.length > 0) setShowSuggestions(true);
                                }}
                                onBlur={() => {
                                    // Delay hiding to allow click events on suggestions to fire
                                    setTimeout(() => setShowSuggestions(false), 200);
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'ArrowDown') {
                                        e.preventDefault();
                                        if (showSuggestions && suggestions.length > 0) {
                                            setActiveSuggestionIndex(prev => prev < suggestions.length - 1 ? prev + 1 : prev);
                                        }
                                    } else if (e.key === 'ArrowUp') {
                                        e.preventDefault();
                                        if (showSuggestions && suggestions.length > 0) {
                                            setActiveSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
                                        }
                                    } else if (e.key === 'Enter') {
                                        e.preventDefault();
                                        if (showSuggestions && activeSuggestionIndex >= 0) {
                                            setRole(suggestions[activeSuggestionIndex]);
                                            setShowSuggestions(false);
                                            setActiveSuggestionIndex(-1);
                                        } else if (role) {
                                            setShowSuggestions(false);
                                            handleScan();
                                        }
                                    } else if (e.key === 'Escape') {
                                        setShowSuggestions(false);
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
                        
                        {/* Suggestions Dropdown */}
                        {showSuggestions && suggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-3 bg-[#0f0f1a]/95 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl z-50 flex flex-col py-2 animate-in fade-in slide-in-from-top-2 duration-200">
                                {suggestions.map((suggestion, index) => {
                                    // Highlight matching part
                                    const matchIndex = suggestion.toLowerCase().indexOf(role.toLowerCase());
                                    const beforeMatch = suggestion.slice(0, matchIndex);
                                    const matchText = suggestion.slice(matchIndex, matchIndex + role.length);
                                    const afterMatch = suggestion.slice(matchIndex + role.length);

                                    return (
                                        <button
                                            key={suggestion}
                                            className={`px-6 py-3 cursor-pointer transition-colors flex items-center gap-3 text-left w-full ${index === activeSuggestionIndex ? 'bg-primary/20 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}
                                            onClick={() => {
                                                setRole(suggestion);
                                                setShowSuggestions(false);
                                                setActiveSuggestionIndex(-1);
                                            }}
                                            onMouseEnter={() => setActiveSuggestionIndex(index)}
                                        >
                                            <Search size={16} className={index === activeSuggestionIndex ? 'text-primary' : 'text-slate-500'} />
                                            <span className="text-base">
                                                {beforeMatch}
                                                <span className="text-primary font-semibold">{matchText}</span>
                                                {afterMatch}
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        )}

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
                                                const id = r.email || r.linkedin_url || `result-${results.indexOf(r)}`;
                                                return selectedEmails.has(id as string);
                                            });

                                            // 2. Create candidates and track successful ones
                                            const creationPromises = selectedResults.map(async (r) => {
                                                try {
                                                    const res = await api.createCandidate({
                                                        name: r.name || 'Unknown Candidate',
                                                        title: r.title || undefined,
                                                        company: r.company || undefined,
                                                        linkedin_url: r.linkedin_url || undefined,
                                                        email: r.email || undefined,
                                                        generated_email: r.generated_email || undefined,
                                                        email_confidence: typeof r.email_confidence === 'number' ? r.email_confidence : undefined,
                                                        summary: r.summary || undefined,
                                                        match_score: typeof r.resonance_score === 'number' && !isNaN(r.resonance_score) 
                                                            ? Math.round(r.resonance_score * 100) 
                                                            : (typeof r.hr_score === 'number' && !isNaN(r.hr_score) ? Math.round(r.hr_score * 100) : 50),
                                                        status: 'new',
                                                        tags: [role]
                                                    });
                                                    
                                                    if (res?.id) {
                                                        return { id: res.id, r }; // Return both tracking ID and original result
                                                    }
                                                } catch (err) {
                                                    console.error(`Failed to create candidate ${r.name}`, err);
                                                    return null;
                                                }
                                                return null;
                                            });

                                            const creationResults = (await Promise.all(creationPromises)).filter(item => item !== null) as {id: number, r: ScanResult}[];
                                            const createdIds = creationResults.map(item => item.id);
                                            const successfulUI_IDs = new Set(creationResults.map(item => (item.r.email || item.r.linkedin_url || `result-${results.indexOf(item.r)}`) as string));
                                            
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
                                                
                                                // Remove ONLY successfully added candidates from search results
                                                setResults(prev => prev.filter(r => {
                                                    const id = (r.email || r.linkedin_url || `result-${prev.indexOf(r)}`) as string;
                                                    return !successfulUI_IDs.has(id);
                                                }));
                                                
                                                setSelectedEmails(new Set());
                                                
                                                // Redirect to Pipeline (Dashboard)
                                                router.push('/');
                                            } else {
                                                setIsAdding(false);
                                                success("No candidates were added successfully.");
                                            }
                                        } catch (e) {
                                            console.error(e);
                                        } finally {
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

                        {renderedResults}
                    </div>
                ) : null}

            </div>



        </main>
    );
};

export interface ExtendedCandidate extends ScanResult {
    id: number;
    match_score?: number;
}

export default SearchPage;
