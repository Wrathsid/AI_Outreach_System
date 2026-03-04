'use client';

import { useState, useEffect } from 'react';
import { api, DashboardStats, FunnelStats } from '@/lib/api';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  LineChart, Line, PieChart, Pie, Cell, Legend, CartesianGrid 
} from 'recharts';
import { ArrowLeft, RefreshCw, TrendingUp, Users, Filter, ArrowRight, Activity, Percent, Building } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { FadeUp, CountUp, HoverSpotlight, StaggerContainer, StaggerItem } from '@/components/Animations';


export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [funnel, setFunnel] = useState<FunnelStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [statsData, funnelData] = await Promise.all([
        api.getStats(),
        api.getFunnelStats()
      ]);
      setStats(statsData);
      setFunnel(funnelData);
    } catch {
      console.error("Failed to fetch analytics");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
  };

  const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6'];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const metricCards = [
    { icon: Users, label: 'Total Candidates', value: funnel?.total_candidates || 0, color: 'text-violet-400', bg: 'bg-violet-500/10' },
    { icon: ArrowRight, label: 'Found → Contacted', value: funnel?.conversions.found_to_contacted || 0, suffix: '%', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { icon: Activity, label: 'Response Rate', value: funnel?.conversions.contacted_to_replied || 0, suffix: '%', color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { icon: Percent, label: 'Weekly Goal', value: stats?.weekly_goal_percent || 0, suffix: '%', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  ];

  return (
    <div className="min-h-screen bg-[#09090b] text-white p-8 font-sans selection:bg-primary/20 relative overflow-hidden">
      {/* Ambient Background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-15%] w-[40%] h-[40%] rounded-full bg-violet-600/5 blur-[120px] animate-ambient-drift" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[35%] h-[35%] rounded-full bg-blue-600/5 blur-[100px] animate-ambient-drift-slow" />
      </div>

      {/* Header */}
      <FadeUp>
        <div className="max-w-7xl mx-auto mb-8 flex items-center justify-between relative z-10">
          <div className="flex items-center gap-4">
            <Link 
              href="/" 
              className="p-2 bg-white/5 border border-white/10 rounded-full text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            >
              <ArrowLeft size={20} />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-linear-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Deep Analytics
              </h1>
              <p className="text-gray-500 text-sm">Insights into your outreach performance and pipeline health.</p>
            </div>
          </div>
          <motion.button 
            onClick={handleRefresh}
            disabled={refreshing}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all border
              ${refreshing 
                ? 'bg-white/5 text-gray-600 cursor-not-allowed border-white/5' 
                : 'bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border-white/10'}
            `}
          >
            <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </motion.button>
        </div>
      </FadeUp>

      {/* Metric Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 relative z-10">
        {metricCards.map((card, i) => (
          <FadeUp key={card.label} delay={0.1 * i}>
            <HoverSpotlight className="rounded-2xl">
              <div className="bg-[#111118] p-6 rounded-2xl border border-white/5 hover:border-white/10 transition-all group">
                <div className="flex items-center gap-3 mb-3 text-gray-400">
                  <div className={`p-2.5 ${card.bg} rounded-xl ${card.color} group-hover:scale-110 transition-transform`}>
                    <card.icon size={20} />
                  </div>
                  <span className="font-medium text-sm">{card.label}</span>
                </div>
                <p className="text-3xl font-bold text-white mt-2 tracking-tight">
                  <CountUp target={card.value} suffix={card.suffix} />
                </p>
              </div>
            </HoverSpotlight>
          </FadeUp>
        ))}
      </div>

      {/* Charts Grid */}
      <StaggerContainer className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        
        {/* Funnel Chart */}
        <StaggerItem>
          <HoverSpotlight className="rounded-2xl">
            <div className="bg-[#111118] p-6 rounded-2xl border border-white/5">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Filter size={18} className="text-violet-400" />
                  Pipeline Funnel
                </h2>
              </div>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={funnel?.funnel}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="rgba(255,255,255,0.03)" />
                    <XAxis type="number" stroke="#666" fontSize={12} tickFormatter={(value) => `${value}`} />
                    <YAxis dataKey="stage" type="category" stroke="#999" fontSize={14} width={80} />
                    <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                        itemStyle={{ color: '#fff' }}
                        cursor={{fill: '#ffffff08'}}
                    />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[0, 6, 6, 0]} barSize={36} animationDuration={1500}>
                        {
                            funnel?.funnel.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))
                        }
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </HoverSpotlight>
        </StaggerItem>

        {/* Industry Breakdown */}
        <StaggerItem>
          <HoverSpotlight className="rounded-2xl">
            <div className="bg-[#111118] p-6 rounded-2xl border border-white/5">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Building size={18} className="text-emerald-400" />
                  Top Industries
                </h2>
              </div>
              <div className="h-[300px] w-full flex items-center justify-center">
                {stats?.top_industries && stats.top_industries.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                        data={stats.top_industries}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="value"
                        animationDuration={1200}
                        >
                        {stats.top_industries.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0)" />
                        ))}
                        </Pie>
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#18181b', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" />
                    </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="text-gray-600 text-center">
                        <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 animate-float">
                          <Building size={24} className="text-gray-700" />
                        </div>
                        <p className="text-sm">No industry data available yet.</p>
                    </div>
                )}
              </div>
            </div>
          </HoverSpotlight>
        </StaggerItem>

        {/* Trend Analysis */}
        <StaggerItem className="lg:col-span-2">
          <HoverSpotlight className="rounded-2xl">
            <div className="bg-[#111118] p-6 rounded-2xl border border-white/5">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <TrendingUp size={18} className="text-amber-400" />
                    Lead Generation Trend
                </h2>
              </div>
              <div className="h-[300px] w-full">
                {stats?.recent_leads && stats.recent_leads.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                        data={stats.recent_leads}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                        <defs>
                          <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#8b5cf6" />
                            <stop offset="100%" stopColor="#3b82f6" />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis 
                            dataKey="date" 
                            stroke="#666" 
                            fontSize={12} 
                            tickFormatter={(value) => {
                                const d = new Date(value);
                                return `${d.getMonth()+1}/${d.getDate()}`;
                            }}
                        />
                        <YAxis stroke="#666" fontSize={12} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#18181b', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                            itemStyle={{ color: '#fff' }}
                            labelStyle={{ color: '#9ca3af' }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="count" 
                          name="Leads Found" 
                          stroke="url(#lineGradient)" 
                          strokeWidth={3} 
                          dot={{ r: 4, fill: '#8b5cf6', stroke: '#0f0f1a', strokeWidth: 2 }} 
                          activeDot={{ r: 7, fill: '#8b5cf6', stroke: '#fff', strokeWidth: 2 }} 
                          animationDuration={2000}
                        />
                    </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-600">
                        <div className="text-center">
                          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 animate-float">
                            <TrendingUp size={24} className="text-gray-700" />
                          </div>
                          <p className="text-sm">Not enough historical data for trends.</p>
                        </div>
                    </div>
                )}
              </div>
            </div>
          </HoverSpotlight>
        </StaggerItem>

      </StaggerContainer>
    </div>
  );
}
