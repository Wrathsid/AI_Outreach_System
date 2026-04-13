'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, UserSearch, PieChart as PieIcon, BarChart3 } from 'lucide-react';
import { api, DashboardStats, UserSettings } from '@/lib/api';
import { FadeUp, TextReveal, StaggerContainer, StaggerItem, CountUp, BlurIn, HoverSpotlight } from './Animations';
import { BarChart, Bar, XAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';



const Dashboard = () => {


  const [stats, setStats] = useState<DashboardStats>({ 
    weekly_goal_percent: 0, 
    people_found: 0, 
    emails_sent: 0, 
    account_health: 100,
    is_safe: true,
    recent_leads: [],
    top_industries: []
  });

  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [backendDown, setBackendDown] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [statsData, settingsData] = await Promise.all([
        api.getStats(),
        api.getSettings()
      ]);
      setStats(statsData);
      setUserSettings(settingsData);
      setBackendDown(false);
    } catch {
      setBackendDown(true);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);



  const today = new Date();
  const options: Intl.DateTimeFormatOptions = { weekday: 'long', month: 'long', day: 'numeric' };
  const dateStr = today.toLocaleDateString('en-US', options);
  const hour = today.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const firstName = userSettings?.full_name?.split(' ')[0] || 'there';

  return (
    <main className="flex-1 flex flex-col h-full overflow-x-hidden p-4 md:p-8 relative overflow-y-auto">
      <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-8 pb-10">
        {backendDown && (
          <div className="flex items-center justify-center p-8 rounded-2xl border border-yellow-500/20 bg-yellow-500/5 text-yellow-400 text-center">
            <p>⚠️ Backend is not running. Start the server to load data.</p>
          </div>
        )}
        
        {/* Page Heading with Text Reveal */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <BlurIn delay={0}>
              <div className="flex items-center gap-3 mb-1">
                <p className="text-slate-400 font-medium text-sm tracking-wider uppercase">{dateStr}</p>
              </div>
            </BlurIn>
            <TextReveal 
              text={`${greeting}, ${firstName}.`}
              className="text-white text-3xl md:text-4xl font-semibold tracking-tight leading-tight"
            />
            <BlurIn delay={0.3}>
              <span className="text-slate-400/60 font-normal text-3xl md:text-4xl block mt-1">Your AI is ready to connect.</span>
            </BlurIn>
          </div>
        </header>

        {/* Hero Section with Stat Row */}
        <div className="flex flex-col gap-6">
          <FadeUp delay={0.2}>
            <section className="w-full relative group">
              {/* Card border shimmer effect */}
              <div className="absolute -inset-px bg-linear-to-r from-emerald-500/20 via-primary/20 to-emerald-500/20 rounded-[2.1rem] blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-pulse"></div>
              
              <div className="w-full bg-linear-to-br from-[#131326] to-[#1a1a36] border border-white/5 rounded-3xl p-10 md:p-14 flex flex-col items-center justify-center text-center relative overflow-hidden shadow-2xl">
                
                {/* Subtle background glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none group-hover:bg-emerald-500/10 transition-colors duration-700"></div>

                <div className="relative z-10 max-w-2xl w-full">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                  >
                    <h2 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                      Ready to Prospect?
                    </h2>
                    <p className="text-slate-400 text-lg mb-8 max-w-md mx-auto">
                      Your AI Discovery engine is primed. Scans LinkedIn & public posts for high-intent hiring managers.
                    </p>
                    <Link href="/search">
                      <motion.button 
                        className="mx-auto w-64 h-14 rounded-2xl bg-emerald-500 hover:bg-emerald-600 transition-all text-white font-bold text-lg shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)] flex items-center justify-center gap-3 group/btn relative overflow-hidden"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000"></div>
                        <span>Find Leads</span>
                        <UserSearch size={22} />
                      </motion.button>
                    </Link>
                  </motion.div>
                </div>


              </div>
            </section>
          </FadeUp>

          {/* Quick Stat Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Found Today', value: stats.people_found, icon: UserSearch, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
              { label: 'Outreach Sent', value: stats.emails_sent, icon: Mail, color: 'text-blue-400', bg: 'bg-blue-400/10' },
              { label: 'Health Score', value: stats.account_health, suffix: '%', icon: BarChart3, color: 'text-purple-400', bg: 'bg-purple-400/10' },
            ].map((stat, i) => (
              <FadeUp key={stat.label} delay={0.3 + i * 0.1}>
                <div className="glass-panel p-5 rounded-2xl border border-white/5 flex items-center gap-4 hover:bg-white/5 transition-all group/stat">
                  <div className={`w-12 h-12 rounded-xl ${stat.bg} ${stat.color} flex items-center justify-center shrink-0 group-hover/stat:scale-110 transition-transform`}>
                    <stat.icon size={24} />
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">{stat.label}</p>
                    <p className="text-2xl font-bold text-white tracking-tight">
                      <CountUp target={stat.value} suffix={stat.suffix} />
                    </p>
                  </div>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>

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
                      {stats.people_found === 0 ? (
                        <Link href="/search" className="text-sm text-primary hover:text-primary/80 transition-colors font-medium">
                          Start searching →
                        </Link>
                      ) : (
                        <>
                          <p className="text-2xl font-bold text-white"><CountUp target={stats.people_found} /></p>
                          <p className="text-slate-400 text-xs text-right">Total Leads</p>
                        </>
                      )}
                   </div>
               </div>
               
                <div className="flex-1 w-full min-h-0">
                  <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={stats.recent_leads}>
                         <defs>
                            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                               <stop offset="0%" stopColor="#10b981" stopOpacity={0.8} />
                               <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.3} />
                            </linearGradient>
                         </defs>
                         <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                         <XAxis 
                            dataKey="date" 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{fill: '#64748b', fontSize: 10}}
                            tickFormatter={(value: string) => {
                               try {
                                 return new Date(value).toLocaleDateString('en-US', {weekday: 'short'});
                               } catch {
                                 return value;
                               }
                            }} 
                            dy={10}
                         />
                         <Tooltip 
                            contentStyle={{backgroundColor: '#0f0f1a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '16px', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)'}}
                            itemStyle={{color: '#fff'}}
                            cursor={{fill: 'rgba(255,255,255,0.03)'}}
                         />
                         <Bar 
                            dataKey="count" 
                            fill="url(#barGradient)" 
                            radius={[6, 6, 0, 0]} 
                            barSize={32}
                            animationDuration={1500}
                         />
                      </BarChart>
                   </ResponsiveContainer>
                  </div>
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
                  <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height={300}>
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
                            formatter={(value: number | string | undefined, name: string | undefined) => {
                               const label = name || "";
                               return [value, label.length > 40 ? `${label.substring(0, 40)}...` : label]
                            }}
                         />
                      </PieChart>
                   </ResponsiveContainer>
                  </div>
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


      </div>



    </main>
  );
};

export default Dashboard;
