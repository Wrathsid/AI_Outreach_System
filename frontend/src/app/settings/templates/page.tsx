'use client';

import { useState } from 'react';
import { useTemplates, Template } from '@/context/TemplateContext';
import { Plus, Trash2, Save, X, Search, Sparkles, Wand2, Info } from 'lucide-react';
import { useToast } from '@/context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function TemplatesPage() {
  const { templates, addTemplate, updateTemplate, deleteTemplate } = useTemplates();
  const { success } = useToast();
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Template>>({});
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleEdit = (t: Template) => {
    setEditingId(t.id);
    setFormData(t);
    setIsCreating(false);
  };

  const handleCreate = () => {
    setEditingId(null);
    setFormData({ name: '', subject: '', body: '' });
    setIsCreating(true);
  };

  const handleSave = () => {
    if (!formData.name || !formData.subject || !formData.body) return;
    
    if (isCreating) {
      addTemplate(formData as Omit<Template, 'id'>);
      success("Template created");
    } else if (editingId) {
      updateTemplate(editingId, formData);
      success("Template updated");
    }
    
    setEditingId(null);
    setIsCreating(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete this template?')) {
      deleteTemplate(id);
      success("Template deleted");
      if (editingId === id) {
        setEditingId(null);
        setIsCreating(false);
      }
    }
  };

  const insertVariable = (variable: string) => {
    setFormData(prev => ({
      ...prev,
      body: (prev.body || '') + ` {{${variable}}} `
    }));
  };

  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    t.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0F0F12] overflow-hidden relative">
      {/* Ambient Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
          <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-purple-900/10 blur-[120px] rounded-full"></div>
          <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-900/10 blur-[100px] rounded-full"></div>
      </div>

      <div className="max-w-[1400px] mx-auto w-full p-6 lg:p-8 flex flex-col h-full z-10">
        <header className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1 tracking-tight">Email Templates</h1>
            <p className="text-slate-400 text-sm">Create and manage your reusable email snippets for faster outreach.</p>
          </div>
          <button 
            onClick={handleCreate}
            className="group bg-white text-black hover:bg-slate-200 px-5 py-2.5 rounded-full flex items-center gap-2 transition-all font-medium shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_25px_rgba(255,255,255,0.2)]"
          >
            <Plus size={18} className="group-hover:rotate-90 transition-transform duration-300" /> 
            <span>New Template</span>
          </button>
        </header>

        <div className="flex-1 flex gap-6 overflow-hidden">
           {/* Sidebar List */}
           <div className="w-1/3 min-w-[320px] max-w-[400px] flex flex-col bg-[#14141A]/50 border border-white/5 rounded-2xl backdrop-blur-xl overflow-hidden shrink-0">
             
             {/* Search */}
             <div className="p-4 border-b border-white/5">
               <div className="relative">
                 <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                 <input 
                   type="text" 
                   placeholder="Search templates..." 
                   value={searchQuery}
                   onChange={e => setSearchQuery(e.target.value)}
                   className="w-full bg-white/5 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:bg-white/10 transition-colors"
                 />
               </div>
             </div>

             {/* List Content */}
             <div className="flex-1 overflow-y-auto p-3 space-y-2">
               {isCreating && (
                 <div className="p-4 rounded-xl border border-primary/50 bg-primary/10 mb-2">
                   <div className="flex items-center gap-2 text-primary font-medium mb-1">
                     <Sparkles size={14} /> New Template...
                   </div>
                   <p className="text-xs text-primary/70">Drafting a new masterpiece</p>
                 </div>
               )}
               
               {filteredTemplates.length === 0 && !isCreating && (
                  <div className="text-center py-10 text-slate-500">
                    <p>No templates found.</p>
                  </div>
               )}

               <AnimatePresence>
                 {filteredTemplates.map(t => (
                   <motion.div 
                     key={t.id}
                     initial={{ opacity: 0, y: 5 }}
                     animate={{ opacity: 1, y: 0 }}
                     onClick={() => handleEdit(t)}
                     className={`p-4 rounded-xl border cursor-pointer transition-all group ${
                       editingId === t.id 
                         ? 'bg-white/10 border-white/20 shadow-lg' 
                         : 'bg-transparent border-transparent hover:bg-white/5 hover:border-white/5'
                     }`}
                   >
                     <div className="flex justify-between items-start mb-1">
                       <h3 className={`font-medium transition-colors ${editingId === t.id ? 'text-white' : 'text-slate-300 group-hover:text-white'}`}>
                         {t.name}
                       </h3>
                       {editingId === t.id && <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5"></div>}
                     </div>
                     <p className="text-xs text-slate-500 line-clamp-1 group-hover:text-slate-400 transition-colors">{t.subject}</p>
                   </motion.div>
                 ))}
               </AnimatePresence>
             </div>
           </div>

           {/* Editor / Empty State */}
           <div className="flex-1 bg-[#14141A]/80 border border-white/5 rounded-2xl p-8 flex flex-col backdrop-blur-xl relative overflow-hidden">
             
             {(editingId || isCreating) ? (
               <div className="flex flex-col h-full gap-6 animate-in fade-in zoom-in-95 duration-200">
                 {/* Toolbar / Header */}
                 <div className="flex justify-between items-start border-b border-white/5 pb-6">
                    <div className="flex-1 mr-8">
                       <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Template Name</label>
                       <input 
                         type="text" 
                         placeholder="e.g. Initial Outreach - CEO" 
                         value={formData.name || ''}
                         onChange={e => setFormData({...formData, name: e.target.value})}
                         className="bg-transparent border-none text-2xl font-bold text-white placeholder-slate-600 focus:outline-none w-full p-0"
                       />
                    </div>
                    <div className="flex gap-2">
                       {editingId && (
                         <button 
                           onClick={() => handleDelete(editingId)} 
                           className="p-2.5 hover:bg-red-500/10 hover:text-red-400 rounded-xl text-slate-500 transition-colors"
                           title="Delete Template"
                         >
                           <Trash2 size={20} />
                         </button>
                       )}
                       <button 
                         onClick={() => { setEditingId(null); setIsCreating(false); }} 
                         className="p-2.5 hover:bg-white/10 rounded-xl text-slate-400 transition-colors"
                         title="Close"
                       >
                         <X size={20} />
                       </button>
                    </div>
                 </div>

                 <div className="flex-1 flex flex-col gap-6 overflow-hidden">
                   {/* Subject */}
                   <div>
                     <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Subject Line</label>
                     <input 
                        type="text" 
                        value={formData.subject || ''}
                        onChange={e => setFormData({...formData, subject: e.target.value})}
                        className="w-full bg-[#0A0A0F] border border-white/10 rounded-xl px-5 py-3 text-white placeholder-slate-600 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all font-medium"
                        placeholder="Quick question about {{company}}..."
                     />
                   </div>

                   {/* Body */}
                   <div className="flex-1 flex flex-col min-h-0">
                     <div className="flex justify-between items-center mb-2">
                        <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider">Email Body</label>
                        
                        {/* Variable Chips */}
                        <div className="flex gap-2">
                          {['name', 'company', 'title'].map(v => (
                            <button
                              key={v}
                              onClick={() => insertVariable(v)}
                              className="text-[10px] font-medium px-2 py-1 rounded-md bg-white/5 text-slate-400 hover:text-primary hover:bg-primary/10 border border-white/5 hover:border-primary/20 transition-all flex items-center gap-1"
                            >
                              <Plus size={8} /> {`{{${v}}}`}
                            </button>
                          ))}
                        </div>
                     </div>
                     <textarea 
                        value={formData.body || ''}
                        onChange={e => setFormData({...formData, body: e.target.value})}
                        className="flex-1 w-full bg-[#0A0A0F] border border-white/10 rounded-xl p-5 text-white placeholder-slate-600 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 resize-none font-mono text-sm leading-relaxed"
                        placeholder="Hi {{name}}, I noticed that {{company}} is hiring..."
                     />
                   </div>
                 </div>

                 <div className="flex justify-between items-center pt-2">
                   <p className="text-xs text-slate-500 flex items-center gap-1.5">
                     <Info size={12} />
                     <span>Variables will be replaced automatically when generating drafts.</span>
                   </p>
                   <button 
                     onClick={handleSave}
                     className="bg-primary hover:bg-blue-600 text-white px-8 py-3 rounded-xl font-medium flex items-center gap-2 transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5"
                   >
                     <Save size={18} />
                     Save Template
                   </button>
                 </div>
               </div>
             ) : (
               /* Empty State / Guide */
               <div className="h-full flex flex-col items-center justify-center text-center">
                 <div className="w-24 h-24 rounded-full bg-linear-to-tr from-slate-800 to-[#1A1A24] flex items-center justify-center mb-6 shadow-2xl border border-white/5 group">
                   <Wand2 size={40} className="text-slate-500 group-hover:text-primary transition-colors duration-500" />
                 </div>
                 <h2 className="text-2xl font-bold text-white mb-2">Select a template to edit</h2>
                 <p className="text-slate-400 max-w-md mb-10">
                   Or create a new one to speed up your workflow. Use variables to personalize your outreach at scale.
                 </p>

                 {/* Tips Grid */}
                 <div className="grid grid-cols-2 gap-4 max-w-2xl w-full">
                    <div className="p-5 rounded-2xl bg-white/5 border border-white/5 text-left hover:bg-white/10 transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center text-green-400 mb-3">
                         <span className="font-mono text-xs font-bold">{`{{}}`}</span>
                      </div>
                      <h4 className="text-white font-medium mb-1">Use Variables</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Personalize emails automatically. We support name, company, title, and more.
                      </p>
                    </div>
                    <div className="p-5 rounded-2xl bg-white/5 border border-white/5 text-left hover:bg-white/10 transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 mb-3">
                         <Sparkles size={16} />
                      </div>
                      <h4 className="text-white font-medium mb-1">Keep it Short</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Best performing cold emails are under 150 words. Be direct and valuable.
                      </p>
                    </div>
                 </div>
               </div>
             )}
           </div>
        </div>
      </div>
    </div>
  );
}
