'use client';

import * as React from 'react';
import { Command } from 'cmdk';
import { useRouter } from 'next/navigation';
import { 
  Search, 
  User, 
  Settings, 
  Zap, 
  Home, 
  Globe 
} from 'lucide-react';

export const CommandPalette = () => {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false);
    command();
  }, []);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Global Command Menu"
      className="fixed inset-0 z-100 flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[640px] bg-[#1a1a24] border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
      >
        <div className="flex items-center px-4 border-b border-white/10">
          <Search className="w-5 h-5 text-slate-400 mr-3" />
          <Command.Input 
            placeholder="Type a command or search..."
            className="w-full h-14 bg-transparent outline-none text-white text-lg placeholder-slate-500"
          />
        </div>
        
        <Command.List className="max-h-[300px] overflow-y-auto p-2 scroll-py-2">
          <Command.Empty className="py-6 text-center text-slate-500 text-sm">
            No results found.
          </Command.Empty>

          <Command.Group heading="Navigation" className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 px-2 mt-2">
            <Command.Item
              onSelect={() => runCommand(() => router.push('/'))}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <Home className="w-4 h-4" />
              <span>Dashboard</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push('/search'))}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <Search className="w-4 h-4" />
              <span>Search Leads</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push('/search?mode=discovery'))}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <Globe className="w-4 h-4" />
              <span>Discovery Mode</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push('/settings'))}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </Command.Item>
          </Command.Group>

          <Command.Group heading="Actions" className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 px-2 mt-4">
            <Command.Item
               onSelect={() => runCommand(() => router.push('/search?create=true'))}
               className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <User className="w-4 h-4" />
              <span>Create New Candidate</span>
            </Command.Item>
             <Command.Item
               onSelect={() => runCommand(() => router.push('/'))}
               className="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-200 hover:bg-primary/20 hover:text-white cursor-pointer transition-colors aria-selected:bg-primary/20 aria-selected:text-white"
            >
              <Zap className="w-4 h-4" />
              <span>Quick Draft</span>
            </Command.Item>
          </Command.Group>
        </Command.List>
        
        <div className="border-t border-white/5 bg-white/5 px-4 py-2 flex justify-between items-center text-[10px] text-slate-500">
           <span>Pro Tip: Use arrow keys to navigate</span>
           <div className="flex items-center gap-2">
             <span className="bg-white/10 px-1.5 py-0.5 rounded">Esc</span> to close
           </div>
        </div>
      </div>
    </Command.Dialog>
  );
};
