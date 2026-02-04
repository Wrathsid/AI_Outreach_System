'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { RefreshCw, Mail, UserSearch, MoreHorizontal, ArrowRight, X, Loader2, PieChart as PieIcon, BarChart3 } from 'lucide-react';
import { api, Draft, ActivityLog, DashboardStats, Candidate } from '@/lib/api';
import { FadeUp, TextReveal, StaggerContainer, StaggerItem, CountUp, MagneticHover, BlurIn } from './Animations';
import { BarChart, Bar, XAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import FunnelChart from './FunnelChart';


const Dashboard = () => {
  const [showDraftsModal, setShowDraftsModal] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [stats, setStats] = useState<DashboardStats>({ 
    weekly_goal_percent: 0, 
    people_found: 0, 
    emails_sent: 0, 
    replies_received: 0,
    recent_leads: [],
    top_industries: []
  });
  const [loading, setLoading] = useState(true);




  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setLoading(true);
    const [draftsData, activityData, statsData, candidatesData] = await Promise.all([
      api.getDrafts(),
      api.getActivity(),
      api.getStats(),
      api.getCandidates()
    ]);
    setDrafts(draftsData);
    setActivity(activityData);
    setStats(statsData);
    setCandidates(candidatesData);
    setLoading(false);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line
    loadData();
  }, [loadData]);



  const formatTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  const today = new Date();
  const options: Intl.DateTimeFormatOptions = { weekday: 'long', month: 'long', day: 'numeric' };
  const dateStr = today.toLocaleDateString('en-US', options);
  const hour = today.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <main className="flex-1 flex flex-col h-full overflow-y-auto overflow-x-hidden p-4 md:p-8 relative">
      <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-8 pb-10">
        
        {/* Page Heading with Text Reveal */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <BlurIn delay={0}>
              <p className="text-slate-400 font-medium text-sm mb-1 tracking-wider uppercase">{dateStr}</p>
            </BlurIn>
            <TextReveal 
              text={`${greeting}, there.`}
              className="text-white text-3xl md:text-4xl font-semibold tracking-tight leading-tight"
            />
            <BlurIn delay={0.3}>
              <span className="text-slate-400/60 font-normal text-3xl md:text-4xl block mt-1">Your AI is ready to connect.</span>
            </BlurIn>
          </div>

        </header>

        {/* Hero Section */}
        <FadeUp delay={0.2}>
          <section className="@container w-full">
            <motion.div 
              className="glass-card-hero rounded-3xl p-1 overflow-hidden relative group"
              whileHover={{ scale: 1.005 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
              <motion.div 
                className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/10 blur-[100px] rounded-full pointer-events-none"
                animate={{ 
                  scale: [1, 1.2, 1],
                  opacity: [0.1, 0.2, 0.1]
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
              />
              
              <div className="flex flex-col md:flex-row h-full rounded-[20px] overflow-hidden bg-[#131326]/40">
                <div className="w-full md:w-2/5 min-h-[240px] md:min-h-[320px] relative overflow-hidden">
                  <motion.div 
                    className="absolute inset-0 bg-cover bg-center" 
                    style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1551434678-e076c223a692?w=800")' }}
                    whileHover={{ scale: 1.1 }}
                    transition={{ duration: 0.7 }}
                  />
                  <div className="absolute inset-0 bg-linear-to-t from-[#131326] via-transparent to-transparent opacity-80 md:bg-linear-to-r"></div>
                  
                  <div className="absolute bottom-6 left-6 z-10">
                    <motion.div 
                      className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/40 backdrop-blur-md border border-white/10 mb-2"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                      <span className="text-xs font-medium text-white">Active Task</span>
                    </motion.div>
                    <h2 className="text-white text-2xl font-bold leading-tight">
                      {drafts.length > 0 ? 'Review Your Drafts' : 'Start Prospecting'}
                    </h2>
                  </div>
                </div>

                <div className="w-full md:w-3/5 p-6 md:p-10 flex flex-col justify-center relative z-10">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <p className="text-slate-400 text-sm font-medium mb-1">Status</p>
                      <p className="text-white text-lg">
                        {loading ? 'Loading...' : drafts.length > 0 ? `${drafts.length} drafts ready for review` : 'Add candidates to get started'}
                      </p>
                    </div>
                    <motion.button 
                      onClick={() => loadData(true)} 
                      className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10 hover:bg-white/10 transition-colors"
                      whileHover={{ rotate: 180 }}
                      whileTap={{ scale: 0.9 }}
                      transition={{ duration: 0.3 }}
                    >
                      <RefreshCw className={`text-white/80 ${loading ? 'animate-spin' : ''}`} size={24} />
                    </motion.button>
                  </div>

                  <div className="flex flex-col gap-4 mb-8">
                    <div className="flex justify-between text-sm text-slate-400">
                      <span>Weekly Progress</span>
                      <span className="text-white">{stats.weekly_goal_percent}%</span>
                    </div>
                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(25,25,230,0.5)]" 
                        initial={{ width: 0 }}
                        animate={{ width: `${stats.weekly_goal_percent}%` }}
                        transition={{ duration: 1.5, ease: [0.25, 0.4, 0.25, 1], delay: 0.5 }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mt-auto">
                    <MagneticHover className="flex-1">
                      {drafts.length > 0 ? (
                          <motion.button 
                            onClick={() => setShowDraftsModal(true)}
                            className="w-full cursor-pointer items-center justify-center rounded-xl h-12 px-6 bg-primary hover:bg-blue-600 transition-all text-white font-medium shadow-glow flex gap-2 group/btn"
                            whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(25,25,230,0.4)' }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <span>Review {drafts.length} Drafts</span>
                            <motion.div
                              animate={{ x: [0, 5, 0] }}
                              transition={{ duration: 1.5, repeat: Infinity }}
                            >
                              <ArrowRight size={20} />
                            </motion.div>
                          </motion.button>
                      ) : (
                          <Link href="/search" className="w-full">
                            <motion.button 
                              className="w-full cursor-pointer items-center justify-center rounded-xl h-12 px-6 bg-emerald-500 hover:bg-emerald-600 transition-all text-white font-medium shadow-[0_0_20px_rgba(16,185,129,0.4)] flex gap-2 group/btn"
                              whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(16,185,129,0.5)' }}
                              whileTap={{ scale: 0.98 }}
                            >
                              <span>Find Leads</span>
                              <UserSearch size={20} />
                            </motion.button>
                          </Link>
                      )}
                    </MagneticHover>
                    <motion.button 
                      className="w-12 h-12 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-colors text-white"
                      whileHover={{ scale: 1.1, rotate: 90 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <MoreHorizontal size={24} />
                    </motion.button>
                  </div>
                </div>
              </div>
            </motion.div>
          </section>
        </FadeUp>

        {/* Analytics Grid */}
        <StaggerContainer className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <StaggerItem>
            <div className="glass-panel rounded-3xl p-6 md:p-8 flex flex-col h-[320px]">
               <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-3">
                     <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                        <BarChart3 size={20} />
                     </div>
                     <div>
                        <h3 className="text-white font-medium">Leads Found</h3>
                        <p className="text-slate-400 text-xs">Last 7 Days</p>
                     </div>
                  </div>
                  <div className="text-right">
                     <p className="text-2xl font-bold text-white"><CountUp target={stats.people_found} /></p>
                     <p className="text-slate-500 text-xs text-right">Total Leads</p>
                  </div>
               </div>
               
               <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                     <BarChart data={stats.recent_leads}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                        <XAxis 
                           dataKey="date" 
                           axisLine={false} 
                           tickLine={false} 
                           tick={{fill: '#94a3b8', fontSize: 10}}
                           tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', {weekday: 'short'})} 
                           dy={10}
                        />
                        <Tooltip 
                           contentStyle={{backgroundColor: '#1e1e2e', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px'}}
                           itemStyle={{color: '#fff'}}
                           cursor={{fill: 'rgba(255,255,255,0.05)'}}
                        />
                        <Bar 
                           dataKey="count" 
                           fill="#3b82f6" 
                           radius={[4, 4, 0, 0]} 
                           barSize={30}
                           animationDuration={1500}
                        />
                     </BarChart>
                  </ResponsiveContainer>
               </div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="glass-panel rounded-3xl p-6 md:p-8 flex flex-col h-[320px]">
               <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-3">
                     <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                        <PieIcon size={20} />
                     </div>
                     <div>
                        <h3 className="text-white font-medium">Top Roles</h3>
                        <p className="text-slate-400 text-xs">Distribution by Job Title</p>
                     </div>
                  </div>
               </div>
               
               <div className="flex-1 w-full min-h-0 relative">
                  <ResponsiveContainer width="100%" height="100%">
                     <PieChart>
                        <Pie
                           data={stats.top_industries}
                           cx="50%"
                           cy="50%"
                           innerRadius={60}
                           outerRadius={80}
                           paddingAngle={5}
                           dataKey="value"
                        >
                           {stats.top_industries.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={[
                                 '#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b'
                              ][index % 5]} stroke="rgba(0,0,0,0)" />
                           ))}
                        </Pie>
                        <Tooltip 
                           contentStyle={{backgroundColor: '#1e1e2e', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px'}}
                           itemStyle={{color: '#fff'}}
                        />
                     </PieChart>
                  </ResponsiveContainer>
                  {/* Center Text */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                     <div className="text-center">
                        <p className="text-2xl font-bold text-white">{stats.top_industries.length}</p>
                        <p className="text-xs text-slate-500">Roles</p>
                     </div>
                  </div>
               </div>
            </div>
          </StaggerItem>
        </StaggerContainer>

        {/* Conversion Funnel */}
        <FadeUp delay={0.25}>
          <section className="mt-4">
            <FunnelChart />
          </section>
        </FadeUp>

        {/* Recent Leads / Pipeline Preview */}
        {candidates.length > 0 && (
            <FadeUp delay={0.3}>
                <section className="mt-4">
                    <div className="flex justify-between items-center mb-4 ml-2">
                        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">New Leads</h3>
                         <Link href="/candidates" className="text-xs text-primary hover:text-white transition-colors">View All</Link>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {candidates.slice(0, 3).map((candidate, i) => (
                             <motion.div 
                                key={candidate.id}
                                className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-primary/30 transition-all group relative overflow-hidden"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 * i }}
                             >
                                <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ArrowRight className="text-primary -rotate-45 group-hover:rotate-0 transition-transform" size={16} />
                                </div>
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 rounded-full bg-linear-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg">
                                        {candidate.name.charAt(0)}
                                    </div>
                                    <div>
                                        <h4 className="text-white font-medium truncate pr-6">{candidate.name}</h4>
                                        <p className="text-slate-400 text-xs truncate">{candidate.title}</p>
                                        <p className="text-slate-500 text-xs mt-1">{candidate.company}</p>
                                        
                                        <div className="mt-3 flex items-center gap-2">
                                            <div className="text-[10px] bg-white/5 px-2 py-1 rounded text-slate-300 border border-white/5">
                                                {candidate.email ? 'Email Found' : 'No Email'}
                                            </div>
                                            {candidate.match_score > 0 && (
                                                <div className="text-[10px] bg-green-500/10 px-2 py-1 rounded text-green-400 border border-green-500/10">
                                                    {candidate.match_score}% Match
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                             </motion.div>
                        ))}
                    </div>
                </section>
            </FadeUp>
        )}

        {/* Activity Feed */}
        <FadeUp delay={0.4}>
          <section className="mt-4">
            <h3 className="text-slate-400 text-sm font-medium mb-4 uppercase tracking-wider ml-2">Recent Activity</h3>
            <div className="glass-panel rounded-2xl p-1">
              <div className="flex flex-col">
                {loading ? (
                  <div className="flex items-center justify-center p-8">
                    <Loader2 className="animate-spin text-primary" size={24} />
                  </div>
                ) : activity.length > 0 ? (
                  <StaggerContainer staggerDelay={0.05}>
                    {activity.map((item) => (
                      <StaggerItem key={item.id}>
                        <Link 
                          href={item.candidate_id ? `/candidates/${item.candidate_id}` : '#'} 
                          className="flex items-center gap-4 p-4 hover:bg-white/5 rounded-xl transition-colors cursor-pointer group"
                        >
                          <motion.div 
                            className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                              item.action_type === 'email_sent' ? 'bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500 group-hover:text-white' :
                              item.action_type === 'draft_created' ? 'bg-blue-500/10 text-primary group-hover:bg-primary group-hover:text-white' :
                              'bg-purple-500/10 text-purple-400 group-hover:bg-purple-500 group-hover:text-white'
                            }`}
                            whileHover={{ scale: 1.1, rotate: 5 }}
                          >
                            {item.action_type === 'lead_found' ? <UserSearch size={20} /> : <Mail size={20} />}
                          </motion.div>
                          <div className="flex-1">
                            <p className="text-white text-sm font-medium">{item.title}</p>
                            <p className="text-slate-500 text-xs">{item.description}</p>
                          </div>
                          <span className="text-slate-500 text-xs">{formatTimeAgo(item.created_at)}</span>
                        </Link>
                      </StaggerItem>
                    ))}
                  </StaggerContainer>
                ) : (
                  <div className="text-center p-8 text-slate-500">
                    <p>No activity yet. Add candidates to get started!</p>
                  </div>
                )}
              </div>
            </div>
          </section>
        </FadeUp>
      </div>

      {/* Drafts Modal */}
      {showDraftsModal && (
        <motion.div 
          className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div 
            className="glass-panel rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <div className="flex justify-between items-center p-6 border-b border-white/10">
              <h2 className="text-xl font-bold text-white">Review Drafts</h2>
              <motion.button 
                onClick={() => setShowDraftsModal(false)} 
                className="text-slate-400 hover:text-white transition-colors"
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
              >
                <X size={24} />
              </motion.button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {drafts.length > 0 ? drafts.map((draft, index) => (
                <motion.div
                  key={draft.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link 
                    href={`/candidates/${draft.candidate_id}`} 
                    onClick={() => setShowDraftsModal(false)}
                    className="block p-4 bg-white/5 hover:bg-white/10 rounded-xl transition-all border border-white/10 hover:border-primary/40 group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="text-white font-medium">{draft.candidate_name || 'Unknown'}</h3>
                        <p className="text-slate-500 text-xs">{draft.candidate_company || 'Unknown Company'}</p>
                      </div>
                      <ArrowRight size={16} className="text-slate-500 group-hover:text-primary transition-colors" />
                    </div>
                    <p className="text-slate-300 text-sm font-medium">{draft.subject}</p>
                    <p className="text-slate-500 text-sm mt-1 line-clamp-1">{draft.body}</p>
                  </Link>
                </motion.div>
              )) : (
                <div className="text-center p-8 text-slate-500">
                  <p>No drafts yet. Generate drafts from candidate profiles!</p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}


    </main>
  );
};

export default Dashboard;
