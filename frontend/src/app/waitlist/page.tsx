'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CheckCircle, Stars, ArrowRight, Home, Share2, Copy, Check, Twitter, Linkedin } from 'lucide-react';

export default function WaitlistSuccess() {
  const [showShareMenu, setShowShareMenu] = useState(false);
  const [copied, setCopied] = useState(false);
  const shareUrl = typeof window !== 'undefined' ? window.location.origin : 'https://cold-emailing.app';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Personal AI - Cold Emailing Assistant',
          text: 'Check out this AI-powered cold emailing tool!',
          url: shareUrl
        });
      } catch {
        setShowShareMenu(true);
      }
    } else {
      setShowShareMenu(true);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex flex-col overflow-hidden bg-background-dark text-white font-display">
      {/* Background Layers */}
      <div className="absolute inset-0 bg-linear-to-b from-[#0f172a] to-[#020617] z-0"></div>
      <div className="absolute top-[-20%] left-[-10%] w-[800px] h-[800px] bg-primary/10 rounded-full blur-[120px] pointer-events-none z-0"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] pointer-events-none z-0"></div>
      
      {/* Content Layout */}
      <div className="relative z-10 flex flex-col h-full grow">
        {/* Header */}
        <header className="flex items-center justify-between px-8 py-6 w-full max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <Link href="/" className="size-8 flex items-center justify-center bg-white/10 rounded-lg border border-white/5 hover:bg-white/20 transition-colors cursor-pointer">
              <Home size={18} className="text-white" />
            </Link>
            <h2 className="text-white text-base font-semibold tracking-tight">Personal AI</h2>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 flex items-center justify-center px-4 py-10 w-full">
          {/* Glassmorphic Card */}
          <div className="glass-panel w-full max-w-[480px] p-8 md:p-12 rounded-2xl flex flex-col items-center text-center relative overflow-hidden group shadow-2xl animate-fade-in-up">
            {/* Top Shine Effect */}
            <div className="absolute top-0 left-0 w-full h-px bg-linear-to-r from-transparent via-white/20 to-transparent"></div>
            
            {/* Icon */}
            <div className="mb-8 relative">
              <div className="absolute inset-0 bg-primary/30 blur-2xl rounded-full"></div>
              <CheckCircle size={72} className="text-primary relative z-10 drop-shadow-[0_0_15px_rgba(25,25,230,0.6)]" />
            </div>

            {/* Content */}
            <div className="space-y-2 mb-6">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 mb-3">
                <Stars size={14} className="text-primary" />
                <span className="text-xs font-medium text-primary uppercase tracking-wider">Founding Member</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight leading-tight">
                You&apos;re on the list.
              </h1>
            </div>

            <div className="max-w-[340px] mx-auto mb-10">
              <p className="text-slate-400 text-sm md:text-base leading-relaxed">
                Your spot is secured. We are currently onboarding users in batches to ensure the highest quality experience.
              </p>
            </div>

            {/* Action Button */}
            <div className="relative w-full">
              <button 
                onClick={handleShare}
                className="w-full group/btn relative flex items-center justify-center gap-2 bg-white text-black hover:bg-white/90 transition-all duration-300 rounded-lg h-12 px-6 font-semibold text-sm shadow-[0_0_20px_rgba(255,255,255,0.1)]"
              >
                <Share2 size={18} />
                <span className="truncate">Spread the word</span>
                <ArrowRight size={18} className="group-hover/btn:translate-x-0.5 transition-transform" />
              </button>

              {/* Share Menu */}
              {showShareMenu && (
                <div className="absolute top-full mt-2 w-full glass-panel rounded-lg p-4 animate-fade-in-up">
                  <div className="flex flex-col gap-3">
                    <button 
                      onClick={handleCopy}
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-left"
                    >
                      {copied ? <Check size={18} className="text-green-400" /> : <Copy size={18} className="text-slate-400" />}
                      <span className="text-sm text-white">{copied ? 'Copied!' : 'Copy link'}</span>
                    </button>
                    <a 
                      href={`https://twitter.com/intent/tweet?text=Check%20out%20this%20AI-powered%20cold%20emailing%20tool!&url=${encodeURIComponent(shareUrl)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <Twitter size={18} className="text-slate-400" />
                      <span className="text-sm text-white">Share on Twitter</span>
                    </a>
                    <a 
                      href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <Linkedin size={18} className="text-slate-400" />
                      <span className="text-sm text-white">Share on LinkedIn</span>
                    </a>
                  </div>
                  <button 
                    onClick={() => setShowShareMenu(false)}
                    className="mt-3 w-full text-center text-xs text-slate-500 hover:text-slate-300"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>

            {/* Secondary Text */}
            <p className="mt-6 text-xs text-slate-500 font-medium">
              You are #<span className="text-slate-300">4,821</span> in line.
            </p>
          </div>
        </main>

        {/* Footer */}
        <footer className="w-full py-8 text-center px-4">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-6">
              <a className="text-slate-500 hover:text-slate-300 text-xs transition-colors" href="#">Privacy Policy</a>
              <a className="text-slate-500 hover:text-slate-300 text-xs transition-colors" href="#">Terms of Service</a>
              <a className="text-slate-500 hover:text-slate-300 text-xs transition-colors" href="#">Contact Support</a>
            </div>
            <p className="text-slate-600 text-xs">© 2024 Personal AI Inc.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
