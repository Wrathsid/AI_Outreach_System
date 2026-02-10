'use client';

import { useState, useEffect } from 'react';
import { api, DashboardStats, FunnelStats } from '@/lib/api';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  LineChart, Line, PieChart, Pie, Cell, Legend, CartesianGrid 
} from 'recharts';
import { ArrowLeft, RefreshCw, TrendingUp, Users, Filter, ArrowRight, Activity, Percent, Building } from 'lucide-react';
import Link from 'next/link';


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

  return (
    <div className="min-h-screen bg-[#09090b] text-white p-8 font-sans selection:bg-primary/20">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard" 
            className="p-2 bg-gray-900 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-3xl font-bold bg-linear-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Deep Analytics
            </h1>
            <p className="text-gray-400">Insights into your outreach performance and pipeline health.</p>
          </div>
        </div>
        <button 
          onClick={handleRefresh}
          disabled={refreshing}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
            ${refreshing ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-gray-900 hover:bg-gray-800 text-gray-300 hover:text-white'}
          `}
        >
          <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Refreshing..." : "Refresh Data"}
        </button>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Metric Cards */}
        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50 hover:border-gray-700 transition-colors">
          <div className="flex items-center gap-3 mb-2 text-gray-400">
            <div className="p-2 bg-violet-500/10 rounded-lg text-violet-400">
                <Users size={20} />
            </div>
            <span className="font-medium text-sm">Total Candidates</span>
          </div>
          <p className="text-3xl font-bold text-white mt-2">{funnel?.total_candidates || 0}</p>
        </div>

        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50 hover:border-gray-700 transition-colors">
          <div className="flex items-center gap-3 mb-2 text-gray-400">
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                <ArrowRight size={20} />
            </div>
            <span className="font-medium text-sm">Conversion (Found → Contacted)</span>
          </div>
          <p className="text-3xl font-bold text-white mt-2">{funnel?.conversions.found_to_contacted || 0}%</p>
        </div>

        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50 hover:border-gray-700 transition-colors">
            <div className="flex items-center gap-3 mb-2 text-gray-400">
                <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
                    <Activity size={20} />
                </div>
                <span className="font-medium text-sm">Response Rate</span>
            </div>
            <p className="text-3xl font-bold text-white mt-2">{funnel?.conversions.contacted_to_replied || 0}%</p>
        </div>

        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50 hover:border-gray-700 transition-colors">
            <div className="flex items-center gap-3 mb-2 text-gray-400">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                    <Percent size={20} />
                </div>
                <span className="font-medium text-sm">Weekly Goal</span>
            </div>
            <p className="text-3xl font-bold text-white mt-2">{stats?.weekly_goal_percent || 0}%</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Funnel Chart */}
        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Filter size={20} className="text-violet-400" />
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
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#333" />
                <XAxis type="number" stroke="#666" fontSize={12} tickFormatter={(value) => `${value}`} />
                <YAxis dataKey="stage" type="category" stroke="#999" fontSize={14} width={80} />
                <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                    cursor={{fill: '#ffffff10'}}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={40}>
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

        {/* Industry Breakdown */}
        <div className="bg-[#111118] p-6 rounded-xl border border-gray-800/50">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Building size={20} className="text-emerald-400" />
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
                    >
                    {stats.top_industries.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                    </Pie>
                    <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
                </ResponsiveContainer>
            ) : (
                <div className="text-gray-500 text-center">
                    <p>No industry data available yet.</p>
                </div>
            )}
          </div>
        </div>

        {/* Trend Analysis */}
        <div className="lg:col-span-2 bg-[#111118] p-6 rounded-xl border border-gray-800/50">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
                <TrendingUp size={20} className="text-amber-400" />
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
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
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
                        contentStyle={{ backgroundColor: '#18181b', borderColor: '#333', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ color: '#9ca3af' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="count" name="Leads Found" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, fill: '#8b5cf6' }} activeDot={{ r: 6 }} />
                </LineChart>
                </ResponsiveContainer>
            ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                    <p>No enough historical data for trends.</p>
                </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
