'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  RefreshCw, Search, X, Cpu, Network, Zap, Plus, Check, Sparkles
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
  const [skillWeights, setSkillWeights] = useState<Record<string, 'low' | 'medium' | 'core'>>(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('cortex_skill_weights');
        if (stored) return JSON.parse(stored);
      } catch { /* ignore */ }
    }
    return {};
  });

  const cycleWeight = (skill: string) => {
    setSkillWeights(prev => {
      const current = prev[skill] || 'medium';
      const next: 'low' | 'medium' | 'core' = current === 'low' ? 'medium' : current === 'medium' ? 'core' : 'low';
      const updated: Record<string, 'low' | 'medium' | 'core'> = { ...prev, [skill]: next };
      try { localStorage.setItem('cortex_skill_weights', JSON.stringify(updated)); } catch { /* ignore */ }
      return updated;
    });
  };

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
    <div className="flex-1 h-full overflow-y-auto overflow-x-hidden relative bg-black text-white font-sans selection:bg-cyan-500/30">
      <NeuralBackground />
      
      <div className="relative z-10 h-full flex flex-col p-6 md:p-12 max-w-5xl mx-auto w-full overflow-y-auto">
        
        {/* Header Section */}
        <header className="flex items-end justify-between mb-10 animate-fade-in-up shrink-0">
          <div>
             <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                    <Cpu size={24} className="text-cyan-400" />
                </div>
                <h1 className="text-4xl font-bold tracking-tight text-white">
                  The Cortex
                </h1>
             </div>
             <p className="text-slate-400 text-sm font-light max-w-md leading-relaxed">
               Define your skills to train the AI on your professional context. The more specific you are, the better your outreach becomes.
             </p>
             
             <div className="mt-6 flex items-center gap-3">
               <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex items-center gap-2 focus-within:border-cyan-500/50 focus-within:bg-white/10 transition-all w-64">
                 <span className="text-slate-500 text-xs uppercase font-mono tracking-wider">User:</span>
                 <input 
                   type="text" 
                   value={userName}
                   onChange={(e) => setUserName(e.target.value)}
                   onBlur={saveName}
                   onKeyDown={(e) => e.key === 'Enter' && saveName()}
                   placeholder="Your Name"
                   className="bg-transparent border-none outline-none text-white text-sm w-full placeholder-slate-600"
                 />
                 {isSavingName && <RefreshCw size={12} className="text-cyan-500 animate-spin" />}
               </div>
             </div>
          </div>

          <div className="flex items-center gap-8">
             {/* Two-Semicircle Completion Indicator */}
             <div className="relative w-16 h-16 flex items-center justify-center group cursor-default">
                <svg viewBox="0 0 64 64" className="w-full h-full">
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
            
            <h2 className="text-xs font-mono text-cyan-500/70 uppercase tracking-widest flex items-center gap-2 mb-1">
                <Network size={12} /> Skill Mapping
            </h2>

            {/* Search Bar */}
            <div ref={dropdownRef} className="relative">
              <div className="relative group">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" />
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
                  className="w-full bg-white/3 border border-white/10 hover:border-white/20 focus:border-cyan-500/50 rounded-xl pl-11 pr-4 py-3.5 text-sm text-white placeholder-slate-600 focus:outline-none transition-all duration-300 focus:shadow-[0_0_20px_-5px_rgba(6,182,212,0.15)]"
                />
                {searchQuery && (
                  <button 
                    onClick={() => { setSearchQuery(''); setShowDropdown(false); }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded-md transition-colors"
                  >
                    <X size={14} className="text-slate-500" />
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
                        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-cyan-500/10 text-left transition-colors group/item"
                      >
                        <Plus size={14} className="text-slate-600 group-hover/item:text-cyan-400 transition-colors shrink-0" />
                        <span className="text-sm text-slate-300 group-hover/item:text-white transition-colors">{skill}</span>
                        <span className="ml-auto text-[10px] text-slate-700 font-mono">
                          {Object.entries(SKILLS_CATALOG).find(([, skills]) => skills.includes(skill))?.[0]}
                        </span>
                      </button>
                    ))}
                    {isCustomSkill && (
                      <button
                        onClick={addCustomSkill}
                        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-emerald-500/10 text-left transition-colors border-t border-white/5 group/custom"
                      >
                        <Sparkles size={14} className="text-emerald-500/60 group-hover/custom:text-emerald-400 transition-colors shrink-0" />
                        <span className="text-sm text-slate-300 group-hover/custom:text-white transition-colors">
                          Add &quot;{searchQuery.trim()}&quot; as custom skill
                        </span>
                        <span className="ml-auto text-[10px] text-emerald-500/50 font-mono">ENTER ↵</span>
                      </button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>


            {/* Category Quick Picks */}
            <div className="flex flex-wrap gap-2">
              {Object.keys(SKILLS_CATALOG).map((category) => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(activeCategory === category ? null : category)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border ${
                    activeCategory === category 
                      ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' 
                      : 'bg-white/3 text-slate-500 border-white/5 hover:border-white/10 hover:text-slate-300'
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
                  <div className="flex flex-wrap gap-2 p-4 bg-white/2 rounded-xl border border-white/5">
                    {SKILLS_CATALOG[activeCategory].map((skill) => {
                      const isSelected = selectedSkills.includes(skill);
                      return (
                        <button
                          key={skill}
                          onClick={() => toggleSkill(skill)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 border flex items-center gap-1.5 ${
                            isSelected 
                              ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30 shadow-[0_0_8px_-3px_rgba(6,182,212,0.3)]' 
                              : 'bg-white/3 text-slate-400 border-white/5 hover:border-cyan-500/20 hover:text-slate-200'
                          }`}
                        >
                          {isSelected && <Check size={10} className="text-cyan-400" />}
                          {skill}
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>


            {/* Selected Skills Display */}
            {selectedSkills.length > 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-3"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono text-slate-500 uppercase tracking-wider flex items-center gap-2">
                    <Zap size={12} className="text-cyan-500" /> 
                    Active Skills ({selectedSkills.length})
                  </h3>
                  <button
                    onClick={saveSkills}
                    disabled={isSaving || saved}
                    className={`px-4 py-1.5 rounded-lg text-xs font-mono uppercase tracking-wide transition-all duration-300 flex items-center gap-2 ${
                      saved 
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/20 hover:border-cyan-500/40'
                    }`}
                  >
                    {isSaving ? (
                      <RefreshCw size={12} className="animate-spin" />
                    ) : saved ? (
                      <><Check size={12} /> Saved</>
                    ) : (
                      <><Zap size={12} /> Save to Cortex</>
                    )}
                  </button>
                </div>
                
                <div className="flex flex-wrap gap-2">
                  <AnimatePresence mode="popLayout">
                    {selectedSkills.map((skill) => {
                      const weight = skillWeights[skill] || 'medium';
                      const weightStyles = {
                        low: 'border-slate-500/20 bg-slate-500/5 text-slate-400',
                        medium: 'border-cyan-500/15 bg-cyan-500/8 text-cyan-400',
                        core: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 shadow-[0_0_10px_-3px_rgba(16,185,129,0.3)]',
                      };
                      const weightLabels = { low: 'L', medium: 'M', core: '★' };
                      return (
                        <motion.div
                          key={skill}
                          layout
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          className={`group/chip flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-mono border transition-all duration-200 ${weightStyles[weight]}`}
                        >
                          <button
                            onClick={() => cycleWeight(skill)}
                            className="w-4 h-4 rounded-full bg-white/10 flex items-center justify-center text-[9px] font-bold hover:bg-white/20 transition-colors shrink-0"
                            title={`Weight: ${weight} — click to cycle`}
                          >
                            {weightLabels[weight]}
                          </button>
                          <span>{skill}</span>
                          <button onClick={() => toggleSkill(skill)} className="ml-0.5 opacity-0 group-hover/chip:opacity-100 transition-opacity">
                            <X size={10} />
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
              <div className="text-center py-16 space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-white/3 border border-white/5 flex items-center justify-center mx-auto mb-4">
                  <Sparkles size={24} className="text-slate-600" />
                </div>
                <p className="text-slate-500 text-sm">No skills mapped yet.</p>
                <p className="text-slate-600 text-xs max-w-sm mx-auto">Search above or browse categories to add your skills. The AI adapts its outreach message tone and context based on what you define here.</p>
              </div>
            )}
        </div>

      </div>
    </div>
  );
}
