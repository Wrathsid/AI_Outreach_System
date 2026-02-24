'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { RefreshCw, Mail, UserSearch, Loader2, PieChart as PieIcon, BarChart3 } from 'lucide-react';
import { api, ActivityLog, DashboardStats } from '@/lib/api';
import { FadeUp, TextReveal, StaggerContainer, StaggerItem, CountUp, BlurIn, HoverSpotlight } from './Animations';
import { BarChart, Bar, XAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';



const Dashboard = () => {


  const [activity, setActivity] = useState<ActivityLog[]>([]);

  const [stats, setStats] = useState<DashboardStats>({ 
    weekly_goal_percent: 0, 
    people_found: 0, 
    emails_sent: 0, 
    account_health: 100,
    is_safe: true,
    recent_leads: [],
    top_industries: []
  });
  const [loading, setLoading] = useState(true);

  // Batch Progress State
  const [batchTask, setBatchTask] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState<{ total: number, completed: number, failed: number, status: string } | null>(null);

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setLoading(true);
    const [activityData, statsData] = await Promise.all([
      api.getActivity(),
      api.getStats()
    ]);
    setActivity(activityData);
    setStats(statsData);
    setLoading(false);
  }, []);

  useEffect(() => {
    // Check for active batch task
    const storedTask = localStorage.getItem('active_batch_task');
    if (storedTask) {
      setBatchTask(storedTask);
    }
  }, []);

  useEffect(() => {
    if (!batchTask) return;

    const interval = setInterval(async () => {
      const status = await api.getBatchStatus(batchTask);
      if (status) {
        setBatchProgress(status);
        if (status.status === 'done' || status.status === 'failed') {
          clearInterval(interval);
          setTimeout(() => {
            setBatchTask(null);
            setBatchProgress(null);
            localStorage.removeItem('active_batch_task');
            loadData(true); // Refresh dashboard when done
          }, 3000);
        }
      } else {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [batchTask, loadData]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      api.getActivity(),
      api.getStats()
    ]).then(([activityData, statsData]) => {
      if (isMounted) {
        setActivity(activityData);
        setStats(statsData);
        setLoading(false);
      }
    });
    return () => { isMounted = false; };
  }, []);

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
    <main className="flex-1 flex flex-col h-full overflow-x-hidden p-4 md:p-8 relative overflow-y-auto">
      <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-8 pb-10">
        
        {/* Page Heading with Text Reveal */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <BlurIn delay={0}>
              <div className="flex items-center gap-3 mb-1">
                <p className="text-slate-400 font-medium text-sm tracking-wider uppercase">{dateStr}</p>
              </div>
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

        {/* Hero Section - Simplified */}
        <FadeUp delay={0.2}>
          <section className="w-full">
            <div className="w-full bg-[#131326] border border-white/5 rounded-3xl p-12 flex flex-col items-center justify-center text-center relative overflow-hidden group">
              
              {/* Subtle background glow */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 blur-[120px] rounded-full pointer-events-none group-hover:bg-primary/10 transition-colors duration-700"></div>

              <div className="relative z-10 max-w-2xl w-full">
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                  Ready to Prospect?
                </h2>
                <p className="text-slate-400 text-lg mb-8">
                   Start your search to find new leads.
                </p>
                <Link href="/search">
                  <motion.button 
                    className="mx-auto w-64 h-14 rounded-2xl bg-emerald-500 hover:bg-emerald-600 transition-all text-white font-medium text-lg shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)] flex items-center justify-center gap-3 group/btn"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Find Leads
                    <UserSearch size={20} />
                  </motion.button>
                </Link>
              </div>

              {/* Refresh Button (Subtle, Top Right) */}
              <div className="absolute top-6 right-6">
                <button 
                  onClick={() => loadData(true)} 
                  className="p-3 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition-colors"
                  title="Refresh Data"
                >
                  <RefreshCw className={`${loading ? 'animate-spin' : ''}`} size={18} />
                </button>
              </div>

            </div>
          </section>
        </FadeUp>

        {/* Batch Progress Bar */}
        {batchProgress && (
           <FadeUp delay={0.1}>
             <div className="w-full bg-blue-500/10 border border-blue-500/30 rounded-2xl p-4 flex items-center gap-4">
               <Loader2 className="animate-spin text-blue-400" size={24} />
               <div className="flex-1">
                 <div className="flex justify-between items-center mb-1">
                   <h3 className="text-white font-medium text-sm">
                     {batchProgress.status === 'done' ? 'Draft Generation Complete!' : 'Generating AI Drafts...'}
                   </h3>
                   <span className="text-blue-400 text-xs font-mono">{batchProgress.completed} / {batchProgress.total}</span>
                 </div>
                 <div className="w-full bg-black/40 rounded-full h-2 overflow-hidden">
                   <div 
                     className={`${batchProgress.status === 'done' ? 'bg-emerald-500' : 'bg-blue-500'} h-full rounded-full transition-all duration-500`}
                     style={{ width: `${(batchProgress.completed / batchProgress.total) * 100}%` }}
                   ></div>
                 </div>
               </div>
             </div>
           </FadeUp>
        )}

        {/* Analytics Grid */}
        <StaggerContainer className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <StaggerItem>
            <HoverSpotlight className="rounded-3xl">
              <div className="glass-panel p-6 md:p-8 flex flex-col h-[320px] relative z-10">
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
            </HoverSpotlight>
          </StaggerItem>

          <StaggerItem>
            <HoverSpotlight className="rounded-3xl">
              <div className="glass-panel p-6 md:p-8 flex flex-col h-[320px] relative z-10">
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
            </HoverSpotlight>
          </StaggerItem>
        </StaggerContainer>




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
                    {activity.slice(0, 10).map((item) => (
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



    </main>
  );
};

export default Dashboard;
