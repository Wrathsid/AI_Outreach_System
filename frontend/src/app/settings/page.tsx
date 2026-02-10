import { useState, useEffect } from 'react';
import { 
  Save, Loader2, User, Building, Mail, CheckCircle2, XCircle, ExternalLink, Sliders, Zap, Brain
} from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';

export default function Settings() {
  const [isSaving, setIsSaving] = useState(false);
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');

  // Voice & Tone State
  const [formality, setFormality] = useState(75);
  const [length, setLength] = useState(30);
  const [useEmoji, setUseEmoji] = useState(false);
  
  // Brain Context State
  const [skillsCount, setSkillsCount] = useState(0);
  
  // Gmail state
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailEmail, setGmailEmail] = useState<string | null>(null);
  const [gmailLoading, setGmailLoading] = useState(true);

  const { success } = useToast();

  useEffect(() => {
    const loadSettings = async () => {
      // Parallel fetch
      const [settingsData, brainData] = await Promise.all([
        api.getSettings(),
        api.getBrainContext()
      ]);

      if (settingsData) {
        setFullName(settingsData.full_name || '');
        setCompany(settingsData.company || '');
        setRole(settingsData.role || '');
      }

      if (brainData) {
        setFormality(brainData.formality);
        setLength(brainData.detail_level);
        setUseEmoji(brainData.use_emojis);
        if (brainData.extracted_skills) {
          setSkillsCount(brainData.extracted_skills.length);
        }
      }
    };
    loadSettings();
  }, []);

  // Load Gmail status
  useEffect(() => {
    const loadGmailStatus = async () => {
      setGmailLoading(true);
      const status = await api.getGmailStatus();
      setGmailConnected(status.connected);
      setGmailEmail(status.email || null);
      setGmailLoading(false);
    };
    loadGmailStatus();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    
    await Promise.all([
      api.updateSettings({
        full_name: fullName,
        company,
        role
      }),
      api.updateBrainContext(formality, length, useEmoji)
    ]);

    await new Promise(r => setTimeout(r, 800));
    setIsSaving(false);
    success("All settings saved successfully");
  };

  const handleConnectGmail = async () => {
    const authUrl = await api.getGmailAuthUrl();
    if (authUrl) {
      window.location.href = authUrl;
    }
  };



  return (
    <div className="flex-1 h-full overflow-y-auto relative scroll-smooth bg-background-dark/50">
      <div className="fixed inset-0 bg-[#0F0F12] -z-20"></div>
      <div className="fixed inset-0 opacity-15 pointer-events-none -z-10" style={{ backgroundImage: 'radial-gradient(at 100% 0%, hsla(280, 50%, 15%, 0.3) 0, transparent 50%), radial-gradient(at 0% 100%, hsla(240, 80%, 10%, 0.3) 0, transparent 50%)' }}></div>
      
      <div className="max-w-5xl mx-auto px-6 py-10 lg:px-12 lg:py-14 flex flex-col gap-10">
        
        {/* Page Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 animate-fade-in-up">
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">Settings</h1>
            <p className="text-gray-400 text-lg font-light leading-relaxed">Manage your account preferences and app configuration.</p>
          </div>
          
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-blue-600 text-white rounded-xl shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all transform hover:-translate-y-0.5"
          >
            {isSaving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
            <span className="font-semibold">Save Changes</span>
          </button>
        </header>

        <div className="max-w-3xl mx-auto flex flex-col gap-8">

            {/* Skills & Context */}
            <section className="glass-panel rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden animate-fade-in-up">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                    <Brain size={120} />
                </div>
                
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-pink-500/10 rounded-lg text-pink-400">
                        <Brain size={20} />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Skills & Context</h2>
                </div>
                
                <p className="text-sm text-gray-400 -mt-2">
                    Your skills are managed in The Cortex. The AI personalizes outreach based on the skills you define there.
                </p>

                <div className="relative z-10 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-300">
                        <Zap size={14} className="text-cyan-400" />
                        <span>{skillsCount > 0 ? `${skillsCount} skills mapped` : 'No skills mapped yet'}</span>
                    </div>
                    <Link 
                        href="/brain"
                        className="px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 rounded-lg text-sm font-medium border border-cyan-500/20 hover:border-cyan-500/40 transition-all flex items-center gap-2"
                    >
                        <Brain size={14} /> Manage in Cortex
                    </Link>
                </div>
            </section>

            {/* Email Integration */}
            <section className="glass-panel rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden animate-fade-in-up delay-100">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                    <Mail size={120} />
                </div>
                
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-red-500/10 rounded-lg text-red-400">
                        <Mail size={20} />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Email Integration</h2>
                </div>

                <div className="relative z-10">
                    {gmailLoading ? (
                        <div className="flex items-center gap-3 text-gray-400">
                            <Loader2 size={20} className="animate-spin" />
                            <span>Checking Gmail connection...</span>
                        </div>
                    ) : gmailConnected ? (
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-green-500/20 rounded-full">
                                    <CheckCircle2 size={20} className="text-green-400" />
                                </div>
                                <div>
                                    <p className="text-white font-medium">Gmail Connected</p>
                                    <p className="text-gray-400 text-sm">{gmailEmail}</p>
                                </div>
                            </div>
                            <p className="text-sm text-gray-500">
                                Emails will be sent directly from your Gmail account for better deliverability.
                            </p>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-500/20 rounded-full">
                                    <XCircle size={20} className="text-red-400" />
                                </div>
                                <div>
                                    <p className="text-white font-medium">Gmail Not Connected</p>
                                    <p className="text-gray-400 text-sm">Connect your Gmail to send emails directly from your account.</p>
                                </div>
                            </div>
                            <button
                                onClick={handleConnectGmail}
                                className="flex items-center gap-2 px-5 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl transition-all w-fit"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                </svg>
                                <span>Connect Gmail</span>
                                <ExternalLink size={14} className="opacity-50" />
                            </button>
                        </div>
                    )}
                </div>
            </section>
            
            {/* Personal Profile */}
            <section className="glass-panel rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden animate-fade-in-up delay-200">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                    <User size={120} />
                </div>
                
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <User size={20} />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Personal Profile</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                     <div className="flex flex-col gap-2">
                        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Full Name</label>
                        <input 
                          className="block w-full px-4 py-3 bg-[#111118] border border-gray-700/50 hover:border-gray-600 focus:border-primary rounded-xl text-white text-sm placeholder-gray-600 focus:ring-1 focus:ring-primary transition-all" 
                          placeholder="John Doe" 
                          type="text"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                        />
                    </div>
                     <div className="flex flex-col gap-2">
                        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Role / Title</label>
                        <input 
                          className="block w-full px-4 py-3 bg-[#111118] border border-gray-700/50 hover:border-gray-600 focus:border-primary rounded-xl text-white text-sm placeholder-gray-600 focus:ring-1 focus:ring-primary transition-all" 
                          placeholder="Founder" 
                          type="text"
                          value={role}
                          onChange={(e) => setRole(e.target.value)}
                        />
                    </div>
                     <div className="flex flex-col gap-2 md:col-span-2">
                        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Company Name</label>
                        <div className="relative">
                            <Building className="absolute left-4 top-3.5 text-gray-500" size={16} />
                            <input 
                              className="block w-full pl-11 pr-4 py-3 bg-[#111118] border border-gray-700/50 hover:border-gray-600 focus:border-primary rounded-xl text-white text-sm placeholder-gray-600 focus:ring-1 focus:ring-primary transition-all" 
                              placeholder="Acme Inc." 
                              type="text"
                              value={company}
                              onChange={(e) => setCompany(e.target.value)}
                            />
                        </div>
                    </div>
                </div>
            </section>
            
            {/* AI Voice & Tone */}
            <section className="glass-panel rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden animate-fade-in-up delay-300">
                <div className="absolute top-0 right-0 p-6 opacity-5">
                    <Sliders size={120} />
                </div>
                
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                        <Zap size={20} />
                    </div>
                    <h2 className="text-xl font-semibold text-white">AI Voice & Tone</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                    {/* Formality */}
                    <div className="flex flex-col gap-4">
                        <div className="flex justify-between items-center">
                            <label className="text-white font-medium">Formality</label>
                            <span className="text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">{formality}%</span>
                        </div>
                        <div className="flex flex-col gap-2">
                            <input 
                                className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                                max="100" 
                                min="0" 
                                type="range" 
                                value={formality}
                                onChange={(e) => setFormality(Number(e.target.value))}
                            />
                            <div className="flex justify-between text-xs font-medium text-gray-500">
                                <span>Casual</span>
                                <span>Formal</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Detail Level */}
                    <div className="flex flex-col gap-4">
                        <div className="flex justify-between items-center">
                            <label className="text-white font-medium">Detail Level</label>
                            <span className="text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">{length}%</span>
                        </div>
                        <div className="flex flex-col gap-2">
                            <input 
                                className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                                max="100" 
                                min="0" 
                                type="range" 
                                value={length}
                                onChange={(e) => setLength(Number(e.target.value))}
                            />
                            <div className="flex justify-between text-xs font-medium text-gray-500">
                                <span>Concise</span>
                                <span>Extensive</span>
                            </div>
                        </div>
                    </div>

                    {/* Emoji Usage */}
                    <div className="flex items-center justify-between md:col-span-2 pt-2">
                        <div>
                            <p className="text-white font-medium">Use Emojis</p>
                            <p className="text-xs text-slate-500">Allow AI to use emojis in non-formal contexts</p>
                        </div>
                        <button
                            onClick={() => setUseEmoji(!useEmoji)}
                            className={`w-12 h-6 rounded-full transition-colors relative ${useEmoji ? 'bg-primary' : 'bg-gray-700'}`}
                        >
                            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${useEmoji ? 'left-7' : 'left-1'}`} />
                        </button>
                    </div>
                </div>
            </section>

        </div>

      </div>
    </div>
  );
}
