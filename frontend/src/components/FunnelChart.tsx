'use client';

import React, { useEffect, useState } from 'react';

interface FunnelStage {
  stage: string;
  count: number;
  percent: number;
}

interface FunnelData {
  funnel: FunnelStage[];
  conversions: {
    found_to_contacted: number;
    contacted_to_replied: number;
    replied_to_meeting: number;
  };
  total_candidates: number;
}

const STAGE_GRADIENTS = [
  'from-blue-500 to-blue-600',
  'from-indigo-500 to-indigo-600',
  'from-purple-500 to-purple-600',
  'from-green-500 to-green-600',
];

export default function FunnelChart() {
  const [data, setData] = useState<FunnelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFunnelData();
  }, []);

  const fetchFunnelData = async () => {
    try {
      const response = await fetch('http://localhost:8000/stats/funnel');
      if (!response.ok) throw new Error('Failed to fetch funnel data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 border border-white/10">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-white/10 rounded w-1/3"></div>
          <div className="h-40 bg-white/10 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 border border-white/10">
        <p className="text-red-400">Error loading funnel: {error}</p>
      </div>
    );
  }

  const maxCount = Math.max(...data.funnel.map(s => s.count), 1);

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Conversion Funnel</h3>
          <p className="text-sm text-white/50">{data.total_candidates} total leads</p>
        </div>
        <button 
          onClick={fetchFunnelData}
          className="text-sm text-white/50 hover:text-white transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Funnel Visualization */}
      <div className="space-y-3">
        {data.funnel.map((stage, index) => (
          <div key={stage.stage} className="relative">
            {/* Stage Row */}
            <div className="flex items-center gap-4">
              {/* Stage Name */}
              <div className="w-32 text-right">
                <span className="text-sm font-medium text-white/70">{stage.stage}</span>
              </div>
              
              {/* Bar Container */}
              <div className="flex-1 relative h-10">
                {/* Background */}
                <div className="absolute inset-0 bg-white/5 rounded-lg"></div>
                
                {/* Filled Bar */}
                <div 
                  className={`absolute inset-y-0 left-0 bg-linear-to-r ${STAGE_GRADIENTS[index]} rounded-lg transition-all duration-700 ease-out`}
                  style={{ 
                    width: `${Math.max((stage.count / maxCount) * 100, 2)}%`,
                  }}
                >
                  {/* Shimmer effect */}
                  <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/10 to-transparent"></div>
                </div>
                
                {/* Count Label */}
                <div className="absolute inset-0 flex items-center justify-between px-4">
                  <span className="text-sm font-bold text-white z-10">{stage.count}</span>
                  <span className="text-sm font-medium text-white/60">{stage.percent}%</span>
                </div>
              </div>
            </div>
            
            {/* Conversion Arrow */}
            {index < data.funnel.length - 1 && (
              <div className="flex items-center gap-4 py-1">
                <div className="w-32"></div>
                <div className="flex-1 flex items-center justify-center">
                  <span className="text-xs text-white/40">
                    ↓ {getConversionRate(data, index)}% converted
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Conversion Summary */}
      <div className="mt-6 pt-4 border-t border-white/10">
        <div className="grid grid-cols-3 gap-4">
          <ConversionStat 
            label="Lead → Contact" 
            value={data.conversions.found_to_contacted} 
          />
          <ConversionStat 
            label="Contact → Reply" 
            value={data.conversions.contacted_to_replied} 
          />
          <ConversionStat 
            label="Reply → Meeting" 
            value={data.conversions.replied_to_meeting} 
          />
        </div>
      </div>
    </div>
  );
}

function getConversionRate(data: FunnelData, fromIndex: number): number {
  const stages = ['found_to_contacted', 'contacted_to_replied', 'replied_to_meeting'];
  const key = stages[fromIndex] as keyof typeof data.conversions;
  return data.conversions[key] || 0;
}

function ConversionStat({ label, value }: { label: string; value: number }) {
  const getColor = (v: number) => {
    if (v >= 30) return 'text-green-400';
    if (v >= 15) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="text-center">
      <p className="text-xs text-white/40 mb-1">{label}</p>
      <p className={`text-lg font-bold ${getColor(value)}`}>{value}%</p>
    </div>
  );
}
