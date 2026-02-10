'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import NextImage from 'next/image';
import { ArrowLeft, Mail, MoreHorizontal, RefreshCw, User, Clock, MessageSquare, GripVertical, Trash2 } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { cleanDisplayName, getNameInitial } from '@/lib/displayUtils';
import { DndContext, DragOverlay, useSensor, useSensors, DragEndEvent, DragStartEvent, useDroppable, pointerWithin, KeyboardSensor, PointerSensor } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useToast } from '@/context/ToastContext';

// --- Kanban Column Component ---
const KanbanColumn = ({ id, title, count, children }: { id: string, title: string, count: number, children: React.ReactNode }) => {
    const { setNodeRef } = useDroppable({ id });
  
    return (
      <div className="flex flex-col h-full min-w-[320px] w-full md:w-[360px] glass-panel rounded-2xl border border-white/5 overflow-hidden transition-colors hover:border-white/10 group">
        {/* Header */}
        <div className={`p-5 border-b border-white/5 flex justify-between items-center backdrop-blur-md sticky top-0 z-10 ${
            id === 'new' ? 'bg-blue-500/5' :
            id === 'contacted' ? 'bg-amber-500/5' :
            id === 'replied' ? 'bg-emerald-500/5' :
            'bg-slate-500/5'
        }`}>
          <div className="flex items-center gap-3">
             <div className={`p-2 rounded-lg ${
                id === 'new' ? 'bg-blue-500/10 text-blue-400' :
                id === 'contacted' ? 'bg-amber-500/10 text-amber-400' :
                id === 'replied' ? 'bg-emerald-500/10 text-emerald-400' :
                'bg-slate-500/10 text-slate-400'
             }`}>
                {id === 'new' && <User size={16} />}
                {id === 'contacted' && <Mail size={16} />}
                {id === 'replied' && <MessageSquare size={16} />}
                {id === 'snoozed' && <Clock size={16} />}
             </div>
             <div>
                <h3 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">{title}</h3>
                <p className="text-[10px] text-slate-500 font-medium">
                    {id === 'new' ? 'Fresh Leads' : 
                     id === 'contacted' ? 'Outreach Sent' : 
                     id === 'replied' ? 'Engagement' : 'Paused'}
                </p>
             </div>
          </div>
          <div className="px-2.5 py-1 rounded-full bg-white/5 border border-white/5 text-xs font-medium text-slate-400">
            {count}
          </div>
        </div>
        
        {/* Droppable Area */}
        <div ref={setNodeRef} className="flex-1 p-3 space-y-3 overflow-y-auto custom-scrollbar">
          {children}
          {count === 0 && (
             <div className="h-32 flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-white/5 rounded-xl m-2">
                <div className="p-3 rounded-full bg-white/5 mb-2">
                    <GripVertical size={16} className="opacity-50" />
                </div>
                <span className="text-xs">Drop here</span>
             </div>
          )}
        </div>
      </div>
    );
};

// --- Draggable Card Component (Memoized) ---
const SortableCandidateCard = React.memo(({ candidate }: { candidate: Candidate }) => {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: candidate.id });
    
    const style = {
      transform: CSS.Translate.toString(transform), // Use Translate instead of Transform for better performance
      transition,
      opacity: isDragging ? 0.3 : 1,
      zIndex: isDragging ? 999 : 1,
    };
  
    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="touch-none relative group">
            <Link href={`/candidates/${candidate.id}`} onClick={(e) => isDragging && e.preventDefault()}>
                <div className={`
                    relative p-4 rounded-xl border transition-all duration-300
                    ${isDragging 
                        ? 'bg-primary/20 border-primary shadow-[0_0_30px_-5px_rgba(59,130,246,0.6)] rotate-2 scale-105' 
                        : 'bg-[#16161a] border-white/5 hover:border-white/20 hover:bg-[#1c1c21] hover:shadow-lg shadow-sm hover:-translate-y-1'
                    }
                `}>
                    
                    {/* Hover Glow Effect */}
                    <div className="absolute inset-0 rounded-xl bg-linear-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                    <div className="flex items-start justify-between gap-3 relative z-10">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="relative">
                                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-white font-bold text-sm shrink-0 border border-white/10 overflow-hidden shadow-inner">
                                    {candidate.avatar_url ? (
                                        <NextImage src={candidate.avatar_url} alt={cleanDisplayName(candidate.name)} width={40} height={40} className="w-full h-full object-cover" />
                                    ) : (
                                        getNameInitial(candidate.name)
                                    )}
                                </div>
                                {candidate.match_score > 80 && (
                                    <div className="absolute -bottom-1 -right-1 bg-[#0f0f12] p-0.5 rounded-full">
                                        <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-[8px] text-black font-bold">
                                            ★
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="min-w-0 flex-1">
                                <h4 className="text-slate-200 font-medium text-sm truncate leading-tight mb-0.5 group-hover:text-white transition-colors">
                                    {cleanDisplayName(candidate.name)}
                                </h4>
                                <p className="text-slate-500 text-xs truncate group-hover:text-slate-400 transition-colors">
                                    {candidate.company || 'Unknown Company'}
                                </p>
                            </div>
                        </div>
                        
                        <div className="flex flex-col items-end gap-1">
                             {candidate.match_score > 0 && (
                                 <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border flex items-center gap-1 ${
                                     candidate.match_score >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-slate-800 text-slate-500 border-slate-700'
                                 }`}>
                                     {candidate.match_score}%
                                 </span>
                             )}
                        </div>
                    </div>
  
                    <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between relative z-10">
                         <div className="text-[11px] text-slate-500 font-medium truncate max-w-[140px] flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-slate-600"></div>
                            {candidate.title || 'No Title'}
                         </div>
                         <div className="text-slate-600 group-hover:text-white transition-colors p-1 hover:bg-white/10 rounded">
                             <MoreHorizontal size={14} />
                         </div>
                    </div>
                </div>
            </Link>
        </div>
    );
});
SortableCandidateCard.displayName = 'SortableCandidateCard';

// --- Main Page ---

const CandidatesPage = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<number | null>(null);
  const { success: successToast } = useToast();

  const loadCandidates = React.useCallback(async () => {
    try {
        const data = await api.getCandidates();
        setCandidates(data);
    } catch (error) {
        console.error("Failed to load candidates", error);
    } finally {
        setLoading(false);
    }
  }, []);

  const handleDeleteAll = async () => {
    if (!window.confirm('Are you sure you want to DELETE ALL candidates? This action cannot be undone.')) return;
    
    setLoading(true);
    const success = await api.deleteAllCandidates();
    if (success) {
      setCandidates([]);
      successToast('All candidates deleted');
    } else {
      console.error("Failed to delete all");
    }
    setLoading(false);
  };

  useEffect(() => {
    let isMounted = true;
    api.getCandidates().then(data => {
      if (isMounted) {
        setCandidates(data);
        setLoading(false);
      }
    });
    return () => { isMounted = false; };
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }), // Prevent accidental drags
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Group candidates by status
  const columns = React.useMemo(() => ({
    new: candidates
      .filter(c => c.status === 'new' || !c.status)
      .sort((a, b) => (b.match_score || 0) - (a.match_score || 0)),
    contacted: candidates.filter(c => c.status === 'contacted'),
    replied: candidates.filter(c => c.status === 'replied'),
    snoozed: candidates.filter(c => c.status === 'snoozed'),
  }), [candidates]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(Number(event.active.id));
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeId = Number(active.id);
    const overId = over.id as string; // Column ID or Candidate ID

    // Find the candidate
    const candidate = candidates.find(c => c.id === activeId);
    if (!candidate) return;

    // Determine new status
    // If dropped on a column container
    let newStatus = overId;
    
    // If dropped on another card, find that card's column
    if (!['new', 'contacted', 'replied', 'snoozed'].includes(overId)) {
         const overCandidate = candidates.find(c => c.id === Number(overId));
         if (overCandidate) {
             newStatus = overCandidate.status || 'new';
         } else {
             return;
         }
    }

    if (candidate.status !== newStatus) {
        // Optimistic Update
        setCandidates(prev => prev.map(c => 
            c.id === activeId ? { ...c, status: newStatus } : c
        ));
        
        // API Call
        try {
            await api.updateCandidateStatus(activeId, newStatus);
            successToast(`Moved to ${newStatus}`);
        } catch (e) {
            console.error(e);
            // Revert on fail
            loadCandidates();
        }
    }
  };

  const activeCandidate = candidates.find(c => c.id === activeId);

  return (
    <main className="flex-1 h-full overflow-hidden flex flex-col relative w-full bg-[#0a0a0f]">
       {/* Background Ambience */}
       <div className="fixed inset-0 pointer-events-none z-0">
            <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/5 blur-[120px]"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/5 blur-[100px]"></div>
       </div>

       {/* Header */}
       <header className="px-8 py-6 flex justify-between items-center border-b border-white/5 bg-[#0f0f12]/50 backdrop-blur-md z-10 shrink-0">
          <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
                  <ArrowLeft size={20} />
              </Link>
              <div className="flex flex-col">
                  <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                    Pipeline 
                    <span className="text-slate-500 font-normal text-sm">/ {candidates.length} Leads</span>
                  </h1>
              </div>
          </div>
          <div className="flex items-center gap-2">
              <button 
                onClick={handleDeleteAll}
                className="p-2 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium mr-2"
                title="Delete All Candidates"
              >
                <Trash2 size={16} />
                <span className="hidden sm:inline">Delete All</span>
              </button>

              <button 
                  onClick={loadCandidates}
                  className={`p-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
              >
                  <RefreshCw size={18} />
              </button>
          </div>
       </header>

       {/* Kanban Board */}
       <div className="flex-1 overflow-x-auto overflow-y-hidden p-6 z-10">
          <DndContext 
            sensors={sensors} 
            collisionDetection={pointerWithin} 
            onDragStart={handleDragStart} 
            onDragEnd={handleDragEnd}
          >
            <div className="flex h-full gap-5 min-w-max pb-4">
                {/* Columns */}
                {(['new', 'contacted', 'replied', 'snoozed'] as const).map(colId => (
                    <KanbanColumn key={colId} id={colId} title={colId} count={columns[colId].length}>
                        <SortableContext items={columns[colId].map(c => c.id)} strategy={verticalListSortingStrategy}>
                            {columns[colId].map(candidate => (
                                <SortableCandidateCard key={candidate.id} candidate={candidate} />
                            ))}
                        </SortableContext>
                    </KanbanColumn>
                ))}
            </div>

            <DragOverlay>
                {activeCandidate ? (
                    <div className="opacity-90 rotate-2 scale-105 cursor-grabbing w-[300px]">
                         <div className="bg-[#1c1c2e] p-4 rounded-xl border border-primary/50 shadow-2xl ring-1 ring-primary">
                             <div className="flex items-center gap-3">
                                 <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-white shrink-0">
                                     {activeCandidate.name.charAt(0)}
                                 </div>
                                 <div className="min-w-0">
                                     <h4 className="text-white font-medium text-sm">{activeCandidate.name}</h4>
                                     <p className="text-slate-400 text-xs">{activeCandidate.company}</p>
                                 </div>
                             </div>
                         </div>
                    </div>
                ) : null}
            </DragOverlay>
          </DndContext>
       </div>
    </main>
  );
};

export default CandidatesPage;
