'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Home, Search } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] bg-violet-900/10 blur-[120px] rounded-full animate-ambient-drift" />
        <div className="absolute bottom-[-20%] right-[10%] w-[400px] h-[400px] bg-blue-900/10 blur-[100px] rounded-full animate-ambient-drift-slow" />
      </div>

      <div className="relative z-10 text-center max-w-lg">
        {/* Animated 404 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8, filter: 'blur(20px)' }}
          animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          transition={{ duration: 0.8, ease: [0.25, 0.4, 0.25, 1] }}
        >
          <h1 className="text-[120px] md:text-[160px] font-bold leading-none tracking-tighter bg-linear-to-b from-white/80 to-white/10 bg-clip-text text-transparent select-none">
            404
          </h1>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          <p className="text-xl font-medium text-white mb-2">Page not found</p>
          <p className="text-slate-500 text-sm mb-8 max-w-sm mx-auto">
            The page you&apos;re looking for doesn&apos;t exist or has been moved. Let&apos;s get you back on track.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="flex items-center justify-center gap-3"
        >
          <Link href="/">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary hover:bg-blue-600 text-white font-semibold text-sm transition-colors shadow-lg shadow-primary/25"
            >
              <Home size={16} />
              Go Home
            </motion.button>
          </Link>
          <Link href="/search">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white font-semibold text-sm transition-all"
            >
              <Search size={16} />
              Search Leads
            </motion.button>
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
