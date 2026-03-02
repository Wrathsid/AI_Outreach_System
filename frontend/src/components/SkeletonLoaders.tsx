'use client';

import React from 'react';

export const Shimmer = ({ className = '' }: { className?: string }) => (
  <div className={`relative overflow-hidden bg-white/5 rounded-lg ${className}`}>
    <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
  </div>
);

// Candidate Detail Skeleton
export const CandidateProfileSkeleton = () => (
  <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 mt-6">
    <div className="lg:col-span-4 space-y-8">
      <div className="space-y-4">
        <Shimmer className="h-8 w-3/4 rounded-lg" />
        <div className="space-y-2">
          <Shimmer className="h-4 w-1/2" />
          <Shimmer className="h-4 w-1/3" />
        </div>
      </div>
      <div className="space-y-4 pt-4 border-t border-white/5">
        <Shimmer className="h-8 w-full rounded-lg" />
        <Shimmer className="h-8 w-full rounded-lg" />
      </div>
    </div>
    <div className="lg:col-span-8">
      <div className="w-full flex-1 bg-[#0f0f15] border border-white/5 rounded-2xl p-6 min-h-[500px] flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-4">
          <Shimmer className="h-8 w-40 rounded-lg" />
          <Shimmer className="h-8 w-24 rounded-lg" />
        </div>
        <div className="space-y-4 mt-4">
          <Shimmer className="h-4 w-full" />
          <Shimmer className="h-4 w-[90%]" />
          <Shimmer className="h-4 w-[95%]" />
          <div className="h-4" />
          <Shimmer className="h-4 w-full" />
          <Shimmer className="h-4 w-[85%]" />
        </div>
      </div>
    </div>
  </div>
);

// Pipeline loading skeleton
export const PipelineSkeleton = () => (
  <div className="space-y-3">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="flex items-center gap-5 p-5 rounded-xl border border-white/5 bg-[#12121a]">
        <Shimmer className="w-12 h-12 rounded-full shrink-0" />
        <div className="flex-1 space-y-2">
          <Shimmer className="h-4 w-1/3" />
          <Shimmer className="h-3 w-1/2" />
        </div>
        <Shimmer className="h-7 w-20 rounded-lg hidden sm:block" />
        <Shimmer className="h-7 w-24 rounded-lg" />
      </div>
    ))}
  </div>
);

// Message generation skeleton
export const MessageSkeleton = () => (
  <div className="w-full flex-1 bg-[#0f0f15] border border-white/5 rounded-2xl px-5 py-4 space-y-3 animate-pulse">
    <Shimmer className="h-4 w-3/4" />
    <Shimmer className="h-4 w-full" />
    <Shimmer className="h-4 w-5/6" />
    <div className="h-4" />
    <Shimmer className="h-4 w-full" />
    <Shimmer className="h-4 w-2/3" />
    <div className="h-4" />
    <Shimmer className="h-4 w-4/5" />
    <Shimmer className="h-4 w-1/2" />
  </div>
);

// Search results skeleton
export const SearchSkeleton = () => (
  <div className="w-full space-y-4">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="flex items-center gap-4 p-5 rounded-xl border border-white/5 bg-[#12121a] animate-pulse">
        <Shimmer className="w-10 h-10 rounded-full shrink-0" />
        <div className="flex-1 space-y-2">
          <Shimmer className="h-4 w-2/5" />
          <Shimmer className="h-3 w-3/5" />
        </div>
        <Shimmer className="h-8 w-16 rounded-lg" />
      </div>
    ))}
  </div>
);

// Dashboard stat card skeleton
export const DashboardSkeleton = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    {[...Array(2)].map((_, i) => (
      <div key={i} className="glass-panel p-6 md:p-8 h-[320px] animate-pulse">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <Shimmer className="w-10 h-10 rounded-xl" />
            <div className="space-y-1">
              <Shimmer className="h-4 w-24" />
              <Shimmer className="h-3 w-16" />
            </div>
          </div>
          <Shimmer className="h-8 w-12" />
        </div>
        <Shimmer className="flex-1 w-full h-[200px] rounded-xl" />
      </div>
    ))}
  </div>
);
