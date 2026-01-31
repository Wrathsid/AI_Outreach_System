'use client';

import { useState, useEffect } from 'react';
import { 
  Save, Loader2, User, Building
} from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';

export default function Settings() {
  const [isSaving, setIsSaving] = useState(false);
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');

  const { success } = useToast();

  useEffect(() => {
    const loadSettings = async () => {
      const data = await api.getSettings();
      if (data) {
        setFullName(data.full_name || '');
        setCompany(data.company || '');
        setRole(data.role || '');
      }
    };
    loadSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    // Real Save
    await api.updateSettings({
      full_name: fullName,
      company,
      role
    });
    
    // Fake delay for other settings
    await new Promise(r => setTimeout(r, 800));
    
    setIsSaving(false);
    success("All settings saved successfully");
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
            
            {/* Personal Profile */}
            <section className="glass-panel rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden animate-fade-in-up delay-100">
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


        </div>

      </div>
    </div>
  );
}
