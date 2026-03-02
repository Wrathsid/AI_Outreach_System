'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  RefreshCw, Search, X, Zap, Plus, Check, Sparkles, BrainCircuit
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import dynamic from 'next/dynamic';
import { SKILLS_CATALOG, ALL_SKILLS } from '@/data/skillsCatalog';

const NeuralBackground = dynamic(() => import('@/components/NeuralBackground'), { ssr: false });

export default function PersonalBrain() {

  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const [userName, setUserName] = useState('');
  const [isSavingName, setIsSavingName] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadBrainContext = useCallback(async () => {
    const context = await api.getBrainContext();
    if (context.extracted_skills && context.extracted_skills.length > 0) {
      setSelectedSkills(context.extracted_skills);
    }
    const settings = await api.getSettings();
    if (settings.full_name) {
      setUserName(settings.full_name);
    }
  }, []);

  useEffect(() => {
    loadBrainContext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleSkill = (skill: string) => {
    setSaved(false);
    setSelectedSkills(prev => 
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  const addCustomSkill = () => {
    const trimmed = searchQuery.trim();
    if (trimmed && !selectedSkills.includes(trimmed)) {
      setSaved(false);
      setSelectedSkills(prev => [...prev, trimmed]);
      setSearchQuery('');
    }
  };

  const saveSkills = async () => {
    setIsSaving(true);
    const success = await api.updateSkills(selectedSkills);
    if (success) {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
    setIsSaving(false);
  };

  const saveName = async () => {
    setIsSavingName(true);
    const currentSettings = await api.getSettings();
    await api.updateSettings({
      ...currentSettings,
      full_name: userName
    });
    setIsSavingName(false);
  };

  // Filter skills based on search query
  const filteredSkills = searchQuery.trim()
    ? ALL_SKILLS.filter(s => 
        s.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !selectedSkills.includes(s)
      )
    : [];

  // Check if typed skill is custom (not in catalog)  
  const isCustomSkill = searchQuery.trim() && 
    !ALL_SKILLS.some(s => s.toLowerCase() === searchQuery.trim().toLowerCase()) &&
    !selectedSkills.some(s => s.toLowerCase() === searchQuery.trim().toLowerCase());

  const hasName = userName.trim().length > 0;
  const hasSkills = selectedSkills.length > 0;

  return (
    <div className="flex-1 h-full overflow-y-auto overflow-x-hidden relative bg-[#04090e] text-white font-sans selection:bg-cyan-500/30">
      <NeuralBackground />
      
      <div className="relative z-10 h-full flex flex-col p-6 md:p-12 max-w-5xl mx-auto w-full overflow-y-auto pb-32">
        
        {/* Header Section */}
        <header className="flex items-start justify-between mb-12 animate-fade-in-up shrink-0">
          <div>
             <div className="flex items-center gap-3 mb-3">
                <BrainCircuit size={32} className="text-cyan-400" />
                <h1 className="text-4xl font-bold tracking-tight text-white drop-shadow-sm">
                  The Cortex
                </h1>
             </div>
             <p className="text-slate-400 text-sm font-light max-w-lg leading-relaxed">
               Define your skills to train the AI on your professional context. The more specific you are, the better your outreach becomes.
             </p>
             
             <div className="mt-8">
               <div className="bg-[#0a0f16]/80 backdrop-blur-sm border border-white/10 rounded-xl px-4 py-3 flex items-center gap-4 focus-within:border-cyan-500/50 focus-within:bg-white/5 transition-all w-fit shadow-sm">
                 <span className="text-slate-500 text-xs uppercase font-bold tracking-widest">User</span>
                 <div className="w-px h-5 bg-white/10"></div>
                 <div className="flex items-center gap-2">
                   <input 
                     type="text" 
                     value={userName}
                     onChange={(e) => setUserName(e.target.value)}
                     onBlur={saveName}
                     onKeyDown={(e) => e.key === 'Enter' && saveName()}
                     placeholder="Your Name"
                     className="bg-transparent border-none outline-none text-white text-sm font-medium w-48 placeholder-slate-600"
                   />
                   {isSavingName && <RefreshCw size={14} className="text-cyan-500 animate-spin" />}
                 </div>
               </div>
             </div>
          </div>

          <div className="flex items-center gap-8 mt-2">
             {/* Two-Semicircle Completion Indicator */}
             <div className="relative w-16 h-16 flex items-center justify-center group cursor-default">
                <svg viewBox="0 0 64 64" className="w-full h-full drop-shadow-md">
                    {/* Background semicircles (dim) */}
                    {/* Left semicircle background */}
                    <path
                      d="M 32 4 A 28 28 0 0 0 32 60"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      className="text-white/5"
                      strokeLinecap="round"
                    />
                    {/* Right semicircle background */}
                    <path
                      d="M 32 4 A 28 28 0 0 1 32 60"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      className="text-white/5"
                      strokeLinecap="round"
                    />
                    
                    {/* Active semicircles */}
                    {/* Left semicircle - fills when NAME is entered */}
                    <path
                      d="M 32 4 A 28 28 0 0 0 32 60"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      className={`transition-all duration-700 ease-out ${hasName ? 'text-cyan-500' : 'text-transparent'}`}
                      strokeLinecap="round"
                    />
                    {/* Right semicircle - fills when SKILLS are added */}
                    <path
                      d="M 32 4 A 28 28 0 0 1 32 60"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      className={`transition-all duration-700 ease-out ${hasSkills ? 'text-cyan-500' : 'text-transparent'}`}
                      strokeLinecap="round"
                    />
                </svg>
                {/* Center icon */}
                <div className="absolute inset-0 flex items-center justify-center">
                    {hasName && hasSkills ? (
                      <Zap size={18} className="text-cyan-400" />
                    ) : (
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
                        {!hasName && !hasSkills ? '0/2' : '1/2'}
                      </span>
                    )}
                </div>
                
                {/* Tooltip */}
                <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-black/90 border border-white/10 rounded text-[10px] text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none space-y-0.5">
                    <div className={`flex items-center gap-1.5 ${hasName ? 'text-cyan-400' : 'text-slate-500'}`}>
                      <span>{hasName ? '✓' : '○'}</span> Name
                    </div>
                    <div className={`flex items-center gap-1.5 ${hasSkills ? 'text-cyan-400' : 'text-slate-500'}`}>
                      <span>{hasSkills ? '✓' : '○'}</span> Skills
                    </div>
                </div>
             </div>
          </div>
        </header>


        {/* Skills Section */}
        <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
            
            <h2 className="text-sm font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2 mb-2">
                <BrainCircuit size={16} /> SKILL MAPPING
            </h2>

            {/* Search Bar */}
            <div ref={dropdownRef} className="relative">
              <div className="relative group">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" />
                <input
                  ref={searchRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && isCustomSkill) {
                      addCustomSkill();
                    }
                  }}
                  placeholder="Search skills or type a custom one..."
                  spellCheck={false}
                  autoComplete="off"
                  className="w-full bg-[#0a0f16]/60 backdrop-blur-md border border-white/10 hover:border-white/20 focus:border-cyan-500/50 rounded-2xl pl-12 pr-4 py-4 text-sm text-white placeholder-slate-500 focus:outline-none transition-all duration-300 focus:shadow-[0_0_20px_-5px_rgba(6,182,212,0.15)]"
                />
                {searchQuery && (
                  <button 
                    onClick={() => { setSearchQuery(''); setShowDropdown(false); }}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded-md transition-colors"
                  >
                    <X size={16} className="text-slate-500" />
                  </button>
                )}
              </div>

              {/* Search Dropdown */}
              <AnimatePresence>
                {showDropdown && searchQuery.trim() && (filteredSkills.length > 0 || isCustomSkill) && (
                  <motion.div 
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="absolute z-50 top-full mt-2 w-full bg-[#0d0d14] border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden max-h-64 overflow-y-auto"
                  >
                    {filteredSkills.slice(0, 8).map((skill) => (
                      <button
                        key={skill}
                        onClick={() => { toggleSkill(skill); setSearchQuery(''); }}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-cyan-500/10 text-left transition-colors group/item"
                      >
                        <Plus size={16} className="text-slate-600 group-hover/item:text-cyan-400 transition-colors shrink-0" />
                        <span className="text-sm text-slate-300 group-hover/item:text-white transition-colors">{skill}</span>
                        <span className="ml-auto text-xs text-slate-600 font-mono">
                          {Object.entries(SKILLS_CATALOG).find(([, skills]) => skills.includes(skill))?.[0]}
                        </span>
                      </button>
                    ))}
                    {isCustomSkill && (
                      <button
                        onClick={addCustomSkill}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-emerald-500/10 text-left transition-colors border-t border-white/5 group/custom"
                      >
                        <Sparkles size={16} className="text-emerald-500/60 group-hover/custom:text-emerald-400 transition-colors shrink-0" />
                        <span className="text-sm text-slate-300 group-hover/custom:text-white transition-colors">
                          Add &quot;{searchQuery.trim()}&quot; as custom skill
                        </span>
                        <span className="ml-auto text-xs text-emerald-500/50 font-mono">ENTER ↵</span>
                      </button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>


            {/* Category Quick Picks */}
            <div className="flex flex-wrap gap-3 mt-2">
              {Object.keys(SKILLS_CATALOG).map((category) => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(activeCategory === category ? null : category)}
                  className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border ${
                    activeCategory === category 
                      ? 'bg-[#061e27] text-cyan-400 border-cyan-500/50 shadow-[0_0_15px_-3px_rgba(6,182,212,0.2)]' 
                      : 'bg-transparent text-slate-400 border-white/10 hover:border-white/20 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>

            {/* Category Dropdown Skills */}
            <AnimatePresence>
              {activeCategory && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="flex flex-wrap gap-3 p-6 bg-[#0a0f16]/40 backdrop-blur-sm rounded-2xl border border-white/5">
                    {SKILLS_CATALOG[activeCategory].map((skill) => {
                      const isSelected = selectedSkills.includes(skill);
                      return (
                        <button
                          key={skill}
                          onClick={() => toggleSkill(skill)}
                          className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border flex items-center gap-2 ${
                            isSelected 
                              ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' 
                              : 'bg-transparent text-slate-300 border-white/10 hover:border-white/30 hover:bg-white/5'
                          }`}
                        >
                          {isSelected ? <Check size={14} className="text-cyan-400" /> : <Plus size={14} className="text-slate-500" />}
                          {skill}
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>


            {/* Divider */}
            <div className="w-full h-px bg-white/5 my-6"></div>

            {/* Selected Skills Display & Save */}
            {selectedSkills.length > 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                  <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2">
                    <Zap size={16} className="text-cyan-400" /> 
                    ACTIVE SKILLS ({selectedSkills.length})
                  </h3>
                  
                  <button
                    onClick={saveSkills}
                    disabled={isSaving || saved}
                    className={`px-8 py-3 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2 shadow-lg ${
                      saved 
                        ? 'bg-emerald-500 text-black' 
                        : 'bg-cyan-500 hover:bg-cyan-400 text-black hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    }`}
                  >
                    {isSaving ? (
                      <RefreshCw size={18} className="animate-spin" />
                    ) : saved ? (
                      <><Check size={18} /> Saved successfully</>
                    ) : (
                      <><Zap size={18} /> Save To Cortex</>
                    )}
                  </button>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <AnimatePresence mode="popLayout">
                    {selectedSkills.map((skill) => {
                      return (
                        <motion.div
                          key={skill}
                          layout
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          className={`group/chip flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all duration-200 border-cyan-500/20 bg-[#061e27]/50 text-cyan-50 shadow-sm`}
                        >
                          <BrainCircuit size={14} className="text-cyan-400 opacity-70" />
                          <span className="text-sm font-medium">{skill}</span>
                          <button 
                            onClick={() => toggleSkill(skill)} 
                            className="ml-1 p-0.5 rounded-md hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                          >
                            <X size={14} />
                          </button>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}

            {/* Empty State */}
            {selectedSkills.length === 0 && (
              <div className="text-center py-20 border border-dashed border-white/10 rounded-2xl bg-[#0a0f16]/30">
                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                  <Sparkles size={24} className="text-slate-500" />
                </div>
                <p className="text-slate-400 text-base font-medium mb-2">No active skills in your Cortex.</p>
                <p className="text-slate-500 text-sm max-w-sm mx-auto">Select categories above or search for custom skills to build your profile.</p>
              </div>
            )}
        </div>

      </div>
    </div>
  );
}
