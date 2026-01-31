import React from 'react';
import Link from 'next/link';
import { Send, ArrowRight } from 'lucide-react';

export default function OutreachSuccess() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center relative w-full h-full p-6 overflow-hidden bg-background-dark/50">
      
      {/* Ambient Background Pulse */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden -z-10">
        <div className="w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-[80px] translate-y-[-50px]"></div>
      </div>

      {/* Success Container */}
      <div className="relative z-10 flex flex-col items-center max-w-lg w-full text-center space-y-10 animate-fade-in-up">
        
        {/* Hero Icon */}
        <div className="relative group">
          <div className="absolute inset-0 bg-primary/40 blur-2xl rounded-full opacity-0 group-hover:opacity-40 transition-opacity duration-700"></div>
          {/* Paper Plane Icon */}
          <Send size={120} className="text-white drop-shadow-[0_0_25px_rgba(25,25,230,0.6)] animate-float" strokeWidth={1} />
          
          {/* Decorative Particles */}
          <svg className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[180px] h-[180px] text-white/20 pointer-events-none" fill="none" viewBox="0 0 100 100">
            <circle className="opacity-30" cx="50" cy="50" r="48" stroke="currentColor" strokeDasharray="4 4" strokeWidth="1"></circle>
          </svg>
        </div>

        {/* Typography */}
        <div className="space-y-4">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight drop-shadow-lg">
            Sent with care.
          </h1>
          <p className="text-slate-400 text-lg font-light max-w-sm mx-auto leading-relaxed">
            Your personalized outreach is on its way. The AI has begun monitoring for engagement.
          </p>
        </div>

        {/* Status Indicator */}
        <div className="w-full max-w-xs mx-auto">
          <div className="glass-panel rounded-2xl p-5 flex flex-col gap-3 shadow-2xl shadow-black/20">
            <div className="flex justify-between items-center px-1">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
                </span>
                <span className="text-sm font-medium text-slate-200">Tracking for replies...</span>
              </div>
              <span className="text-xs text-slate-500 font-mono">0%</span>
            </div>
            {/* Progress Bar Component */}
            <div className="h-1.5 w-full bg-slate-700/50 rounded-full overflow-hidden">
              <div className="h-full bg-linear-to-r from-primary to-indigo-400 rounded-full w-[15%] shadow-[0_0_10px_rgba(25,25,230,0.5)]"></div>
            </div>
          </div>
        </div>

        {/* Primary Action */}
        <Link href="/" className="px-8 py-3.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/10 text-white font-medium text-sm tracking-wide flex items-center gap-2 group hover:scale-[1.02] active:scale-[0.98] transition-all backdrop-blur-md">
          <span>Return to Dashboard</span>
          <ArrowRight size={18} className="text-slate-400 group-hover:text-white transition-colors" />
        </Link>
      </div>

      {/* Footer / Decorative Bottom Elements */}
      <div className="fixed bottom-0 left-0 w-full h-32 bg-linear-to-t from-background-dark to-transparent pointer-events-none z-0"></div>
    </div>
  );
}
