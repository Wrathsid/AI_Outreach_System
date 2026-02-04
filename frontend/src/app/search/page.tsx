'use client';

import React, { useState } from 'react';
import { Search, Globe, Loader2, Mail, User, Briefcase, Check } from 'lucide-react';
import { API_BASE, api } from '@/lib/api';
import { FadeUp, BlurIn } from '@/components/Animations';
import { useToast } from '@/context/ToastContext';
import Link from 'next/link';

// Reuse ScanResult type or similar
interface ScanResult {
    name: string;
    title: string;
    company: string;
    email?: string;
    linkedin_url: string;
    summary?: string;
    is_hr?: boolean;
    hr_score?: number;
}

// Common roles for auto-complete
const ROLE_SUGGESTIONS = [
    "Software Engineer",
    "Product Manager",
    "Data Scientist",
    "DevOps Engineer",
    "Sales Representative",
    "Marketing Manager",
    "Technical Recruiter",
    "HR Manager",
    "Account Executive",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Growth Marketer",
    "Customer Success Manager"
];

const SearchPage = () => {
    // const router = useRouter(); // Unused after removing View Results toast
    const [role, setRole] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [results, setResults] = useState<ScanResult[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    const [broadMode, setBroadMode] = useState(false);
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
    
    const [statusMessage, setStatusMessage] = useState('');

    // Filter suggestions based on input
    const filteredSuggestions = ROLE_SUGGESTIONS.filter(s => 
        s.toLowerCase().includes(role.toLowerCase()) && 
        s.toLowerCase() !== role.toLowerCase()
    ).slice(0, 5);

    // Simple scan handler (HR Search default)
    const handleScan = async () => {
        if (!role) return;
        setShowSuggestions(false);
        setIsScanning(true);
        setStatusMessage('Initializing deep scan...');
        setResults([]);
        
        try {
            const queryParams = new URLSearchParams({ 
                role,
                broad_mode: broadMode.toString()
            });
            const response = await fetch(`${API_BASE}/discovery/hr-search?${queryParams.toString()}`);
            
            if (!response.body) throw new Error("No response body");
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const msg = JSON.parse(line);
                        if (msg.type === 'result') {
                            setResults(prev => [...prev, msg.data]);
                        } else if (msg.type === 'status') {
                            setStatusMessage(msg.data);
                        } else if (msg.type === 'done') {
                            setStatusMessage('Scan complete.');
                        }
                    } catch (e) {
                        console.error("Parse error", e);
                    }
                }
            }
        } catch (e) {
            console.error(e);
            setStatusMessage('Scan failed.');
        } finally {
            setIsScanning(false);
            setTimeout(() => setStatusMessage(''), 3000);
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
                
                {/* Header Pills */}
                <BlurIn delay={0}>
                    <div className="inline-flex items-center gap-1 bg-white/5 border border-white/10 rounded-full px-1 py-1 mb-8">
                        <Link href="/candidates" className="px-4 py-1.5 rounded-full text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer">Pipeline</Link>
                        <span className="px-4 py-1.5 rounded-full text-xs font-medium bg-primary text-white shadow-lg shadow-blue-500/20 cursor-default">Discovery</span>
                    </div>
                </BlurIn>

                <BlurIn delay={0.1}>
                    <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">
                        Scan the deep web.
                    </h1>
                </BlurIn>
                
                <BlurIn delay={0.2}>
                    <p className="text-lg text-slate-400 mb-10">
                        Find new leads across LinkedIn, GitHub, and the web.
                    </p>
                </BlurIn>

                {/* Search Input */}
                <FadeUp delay={0.3} className="w-full relative group">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    <div className="relative z-20">
                        <div className="relative flex items-center bg-black/40 border border-white/10 rounded-full p-2 pl-6 backdrop-blur-xl shadow-2xl ring-1 ring-white/5 focus-within:ring-primary/50 transition-all">
                            <Search className="text-slate-500" size={24} />
                            <input 
                                type="text" 
                                value={role}
                                onChange={(e) => {
                                    setRole(e.target.value);
                                    setShowSuggestions(true);
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                onKeyDown={(e) => e.key === 'Enter' && handleScan()}
                                className="flex-1 bg-transparent border-none outline-none text-white px-4 py-4 text-lg placeholder-slate-600"
                                placeholder="Enter role (e.g. 'DevOps Engineer')"
                            />
                            <div className="flex items-center gap-2 mr-2">
                                <button 
                                    onClick={() => setBroadMode(!broadMode)}
                                    className={`text-xs font-medium px-3 py-1.5 rounded-full transition-all border ${
                                        broadMode 
                                            ? 'bg-purple-500/20 text-purple-300 border-purple-500/50' 
                                            : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10'
                                    }`}
                                >
                                    {broadMode ? 'Broad Mode' : 'Precision'}
                                </button>
                            </div>
                            <button 
                                onClick={handleScan}
                                disabled={isScanning || !role}
                                className="bg-primary hover:bg-blue-600 text-white rounded-full px-8 py-4 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
                            >
                                {isScanning ? <Loader2 className="animate-spin" /> : 'Scan'}
                            </button>
                        </div>
                        
                        {/* Status Message */}
                        {isScanning && statusMessage && (
                            <FadeUp delay={0.1} className="mt-4 text-center">
                                <p className="text-sm text-slate-400 font-mono animate-pulse">{statusMessage}</p>
                            </FadeUp>
                        )}

                        {/* Dropdown Suggestions */}
                        {showSuggestions && role && filteredSuggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-[#0a0a0f] border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                                {filteredSuggestions.map((suggestion, index) => (
                                    <button
                                        key={index}
                                        onClick={() => {
                                            setRole(suggestion);
                                            setShowSuggestions(false);
                                        }}
                                        className="w-full text-left px-6 py-3 text-slate-300 hover:bg-white/5 hover:text-white transition-colors flex items-center gap-2"
                                    >
                                        <Search size={14} className="opacity-50" />
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </FadeUp>

                {/* Real-time Results Stack */}
                {results.length > 0 ? (
                    <div className="w-full mt-8 space-y-4 pb-20 override-scroll">
                        
                        {/* Bulk Action Bar */}
                        <div className="flex items-center justify-between px-2 mb-2 animate-in fade-in slide-in-from-bottom-2">
                             <div className="flex items-center gap-3">
                                <button 
                                    onClick={toggleSelectAll}
                                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors group"
                                >
                                    <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${isAllSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-600 group-hover:border-slate-400'}`}>
                                        {isAllSelected && <Check size={10} className="text-white" strokeWidth={3} />}
                                    </div>
                                    <span>Select All ({results.length})</span>
                                </button>
                             </div>
                             
                             {selectedEmails.size > 0 && (
                                <button 
                                    onClick={async () => {
                                        let count = 0;
                                        for (const r of results) {
                                            const id = r.email || r.linkedin_url;
                                            if (selectedEmails.has(id)) {
                                                const res = await api.createCandidate({
                                                    name: r.name,
                                                    title: r.title,
                                                    company: r.company,
                                                    linkedin_url: r.linkedin_url,
                                                    email: r.email,
                                                    summary: r.summary,
                                                    match_score: r.hr_score || 50,
                                                    status: 'new'
                                                });
                                                if (res) count++;
                                            }
                                        }
                                        success(`Added ${count} leads to pipeline`);
                                        setSelectedEmails(new Set());
                                    }}
                                    className="bg-white text-black text-xs font-bold px-4 py-1.5 rounded-full hover:bg-slate-200 transition-colors shadow-lg shadow-white/10 animate-in zoom-in-50"
                                >
                                    Add to Pipeline ({selectedEmails.size})
                                </button>
                             )}
                        </div>

                        {results.map((r, i) => {
                            const id = r.email || r.linkedin_url;
                            const isSelected = selectedEmails.has(id);
                            return (
                                <FadeUp key={i} delay={0.1 * (i % 5)}>
                                    <div 
                                        onClick={() => toggleSelection(id)}
                                        className={`group border backdrop-blur-md rounded-xl p-5 transition-all w-full text-left relative overflow-hidden cursor-pointer ${isSelected ? 'bg-blue-500/10 border-blue-500/30' : 'bg-white/5 hover:bg-white/10 border-white/10 hover:border-white/20'}`}
                                    >
                                        <div className={`absolute inset-0 bg-linear-to-r from-blue-500/5 to-purple-500/5 transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`} />
                                        
                                        <div className="relative z-10 flex gap-4">
                                            {/* Checkbox */}
                                            <div className="pt-1">
                                                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-600 group-hover:border-slate-400'}`}>
                                                    {isSelected && <Check size={12} className="text-white" strokeWidth={3} />}
                                                </div>
                                            </div>

                                            <div className="flex-1">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-10 w-10 rounded-full bg-linear-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center border border-white/5 shadow-inner shadow-white/5">
                                                            <User size={18} className="text-blue-300" />
                                                        </div>
                                                        <div>
                                                            <h3 className="text-white font-medium text-lg leading-tight tracking-tight">{r.name}</h3>
                                                            <div className="flex items-center gap-2 text-slate-400 text-sm mt-0.5">
                                                                <Briefcase size={12} />
                                                                <span className="font-medium text-slate-300">{r.title}</span>
                                                                {r.company && <span className="text-slate-500">• {r.company}</span>}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {r.email && (
                                                        <div 
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                navigator.clipboard.writeText(r.email!);
                                                                success(`Copied ${r.email}`);
                                                            }} 
                                                            className="bg-green-500/10 border border-green-500/20 text-green-400 text-xs px-2.5 py-1.5 rounded-md font-mono flex items-center gap-1.5 shadow-sm shadow-green-900/20 hover:bg-green-500/20 transition-colors cursor-copy" 
                                                            title="Copy Email"
                                                        >
                                                            <Mail size={11} />
                                                            {r.email}
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                {r.summary && (
                                                    <div className="mt-2 pl-13 relative z-10">
                                                        <p className="text-slate-500 text-sm leading-relaxed line-clamp-2">
                                                            {r.summary.length > 140 ? r.summary.substring(0, 140) + "..." : r.summary}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </FadeUp>
                            );
                        })}
                    </div>
                ) : (
                    !isScanning && (
                        <FadeUp delay={0.4} className="mt-12 flex flex-col items-center justify-center gap-4 opacity-50">
                            <Globe size={48} className="text-slate-600" strokeWidth={1} />
                            <p className="text-sm text-slate-600 font-medium tracking-wide">Enter a role to scan the deep web.</p>
                        </FadeUp>
                    )
                )}

            </div>



        </main>
    );
};

export default SearchPage;
