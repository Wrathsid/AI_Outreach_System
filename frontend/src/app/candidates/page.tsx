'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import NextImage from 'next/image';
import { ArrowLeft, Mail, MoreHorizontal, RefreshCw, User, Clock, MessageSquare } from 'lucide-react';
import { api, Candidate } from '@/lib/api';
import { BlurIn } from '@/components/Animations';
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useToast } from '@/context/ToastContext';

// --- Kanban Column Component ---
const KanbanColumn = ({ id, title, count, children }: { id: string, title: string, count: number, children: React.ReactNode }) => {
    const { setNodeRef } = useDroppable({ id });
  
    return (
      <div className="flex flex-col h-full min-w-[300px] w-full md:w-[350px] bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
        {/* Header */}
        <div className={`p-4 border-b border-white/5 flex justify-between items-center ${
            id === 'new' ? 'bg-blue-500/10 text-blue-400' :
            id === 'contacted' ? 'bg-amber-500/10 text-amber-400' :
            id === 'replied' ? 'bg-emerald-500/10 text-emerald-400' :
            'bg-slate-500/10 text-slate-400'
        }`}>
          <div className="flex items-center gap-2 font-semibold tracking-wide uppercase text-xs">
             {id === 'new' && <User size={14} />}
             {id === 'contacted' && <Mail size={14} />}
             {id === 'replied' && <MessageSquare size={14} />}
             {id === 'snoozed' && <Clock size={14} />}
             {title}
          </div>
          <span className="bg-white/10 text-white/70 text-[10px] font-bold px-2 py-0.5 rounded-full">{count}</span>
        </div>
        
        {/* Droppable Area */}
        <div ref={setNodeRef} className="flex-1 p-3 space-y-3 overflow-y-auto">
          {children}
        </div>
      </div>
    );
};

// --- Draggable Card Component ---
const SortableCandidateCard = ({ candidate }: { candidate: Candidate }) => {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: candidate.id });
    
    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
      opacity: isDragging ? 0.4 : 1,
    };
  
    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="touch-none">
            <Link href={`/candidates/${candidate.id}`} onClick={(e) => isDragging && e.preventDefault()}>
                <div className={`group relative bg-[#1c1c2e] hover:bg-[#252538] p-4 rounded-xl border border-white/5 hover:border-white/20 transition-all cursor-grab active:cursor-grabbing shadow-sm hover:shadow-lg ${isDragging ? 'ring-2 ring-primary rotate-2' : ''}`}>
                    
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-white font-bold text-sm shrink-0 border border-white/10 overflow-hidden">
                                {candidate.avatar_url ? (
                                    <NextImage src={candidate.avatar_url} alt={candidate.name} width={40} height={40} className="w-full h-full object-cover" />
                                ) : (
                                    candidate.name.charAt(0)
                                )}
                            </div>
                            <div className="min-w-0">
                                <h4 className="text-white font-medium text-sm truncate leading-tight mb-0.5">{candidate.name}</h4>
                                <p className="text-slate-400 text-xs truncate">{candidate.company}</p>
                            </div>
                        </div>
                        {candidate.match_score > 0 && (
                             <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                                 candidate.match_score >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-slate-700 text-slate-400 border-slate-600'
                             }`}>
                                 {candidate.match_score}%
                             </span>
                        )}
                    </div>
  
                    <div className="mt-3 flex items-center justify-between">
                         <div className="text-[10px] text-slate-500 font-medium truncate max-w-[120px]">
                            {candidate.title}
                         </div>
                         <div className="text-slate-600 hover:text-white transition-colors">
                             <MoreHorizontal size={14} />
                         </div>
                    </div>
                </div>
            </Link>
        </div>
    );
};

// --- Main Page ---
import { useDroppable } from '@dnd-kit/core';

const CandidatesPage = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<number | null>(null);
  const { success } = useToast();

  const loadCandidates = React.useCallback(async () => {
    setLoading(true);
    try {
        const data = await api.getCandidates();
        setCandidates(data);
    } catch (error) {
        console.error("Failed to load candidates", error);
    } finally {
        setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCandidates();
  }, [loadCandidates]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }), // Prevent accidental drags
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Group candidates by status
  const columns = {
    new: candidates.filter(c => c.status === 'new' || !c.status),
    contacted: candidates.filter(c => c.status === 'contacted'),
    replied: candidates.filter(c => c.status === 'replied'),
    snoozed: candidates.filter(c => c.status === 'snoozed'),
  };

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
    const newStatus = overId;
    
    // If dropped on another card, find that card's column
    if (typeof overId === 'number' || !['new', 'contacted', 'replied', 'snoozed'].includes(overId)) {
         return; 
    }

    if (candidate.status !== newStatus) {
        // Optimistic Update
        setCandidates(prev => prev.map(c => 
            c.id === activeId ? { ...c, status: newStatus } : c
        ));
        
        // API Call
        try {
            await api.updateCandidateStatus(activeId, newStatus);
            success(`Moved to ${newStatus}`);
        } catch (e) {
            console.error(e);
            // Revert on fail
            loadCandidates();
        }
    }
  };

  const activeCandidate = candidates.find(c => c.id === activeId);

  return (
    <main className="flex-1 h-full overflow-hidden flex flex-col relative">
       {/* Header */}
       <header className="px-8 py-6 flex justify-between items-center border-b border-white/5 bg-[#0f0f12]/50 backdrop-blur-md z-10">
          <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-slate-400 hover:text-white transition-colors">
                  <ArrowLeft size={20} />
              </Link>
              <BlurIn>
                  <h1 className="text-2xl font-bold text-white tracking-tight">Pipeline</h1>
              </BlurIn>
              <div className="h-6 w-px bg-white/10 mx-2"></div>
              <p className="text-slate-400 text-sm">Drag and drop to manage leads</p>
          </div>
          <button 
                onClick={loadCandidates}
                className={`p-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
             >
                <RefreshCw size={18} />
          </button>
       </header>

       {/* Kanban Board */}
       <div className="flex-1 overflow-x-auto overflow-y-hidden p-6">
          <DndContext 
            sensors={sensors} 
            collisionDetection={closestCorners} 
            onDragStart={handleDragStart} 
            onDragEnd={handleDragEnd}
          >
            <div className="flex h-full gap-6 min-w-max">
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
                    <div className="opacity-90 rotate-2 scale-105 cursor-grabbing">
                         <div className="bg-[#1c1c2e] p-4 rounded-xl border border-primary/50 shadow-2xl ring-2 ring-primary">
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
