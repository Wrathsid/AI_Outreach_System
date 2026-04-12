'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, Settings, Brain, Menu, X, Users, Search } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MagneticHover } from './Animations';

const Sidebar = () => {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        await fetch('http://localhost:8000/health', { signal: controller.signal });
        clearTimeout(timeoutId);
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);


  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);



  const isActive = (path: string) => pathname === path;

  const navItems = [
    { href: '/', icon: Home, label: 'Dashboard' },
    { href: '/search', icon: Search, label: 'Search' },
    { href: '/candidates', icon: Users, label: 'Pipeline' },


    { href: '/brain', icon: Brain, label: 'Personal Brain' },

  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <motion.button 
        onClick={() => setIsMobileOpen(true)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white/10 text-white backdrop-blur-sm"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <Menu size={24} />
      </motion.button>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div 
            className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.nav 
        className={`
          fixed md:relative z-50 md:z-auto
          flex flex-col gap-6 w-[240px] md:w-[88px] h-screen md:h-[calc(100vh-32px)] 
          md:my-4 md:ml-4 glass-panel md:rounded-2xl items-center py-8 shrink-0 
          shadow-glass border-r border-r-white/10
        `}
        initial={false}
        animate={{ 
          x: isMobileOpen ? 0 : isMobile ? -240 : 0 
        }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      >
        {/* Close button for mobile */}
        <motion.button 
          onClick={() => setIsMobileOpen(false)}
          className="md:hidden absolute top-4 right-4 p-2 text-white/60 hover:text-white"
          whileHover={{ scale: 1.1, rotate: 90 }}
          whileTap={{ scale: 0.9 }}
        >
          <X size={24} />
        </motion.button>

        {/* Logo / User Avatar */}
        <motion.div 
          className="mb-6 relative group"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
        >
          <MagneticHover>
            <motion.div 
              className="bg-center bg-no-repeat bg-cover rounded-full size-12 shadow-lg ring-2 ring-white/10" 
              style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBXRt6dLsnIlX1FqjzEzocSMwA4U5jYadog5VnpuINqK2rcNy2lJyVmKHo-cSc7nOZEkRIWPFZP8btRf2iNM5eHJz5rvIsBx7V620ZutDXFBoJISXi4vx2GzPSHvRz7LXDpcs7RrfO4n-5eUoiFCl3awvnp731qmHDjJA671Z83FqNI7wavnAL_wqXyc3n6VyQd4HuGuws3BKB2wrzydcq8KouwQPiYXbXbbVTbDKOt-BB6OtqHMqTUuHFkLZq0ymACETLUYcxBrPXv")' }}
              whileHover={{ scale: 1.1 }}
              transition={{ type: 'spring', stiffness: 400, damping: 17 }}
            />
          </MagneticHover>
          <motion.div
            className={`absolute bottom-0 right-0 w-3 h-3 border-2 border-[#1a1a2e] rounded-full ${backendOnline ? 'bg-green-400' : 'bg-red-400'}`}
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            title={backendOnline ? 'Backend online' : 'Backend offline'}
          />
        </motion.div>

        {/* Nav Items */}
        <div className="flex flex-col gap-4 w-full px-4 items-center md:items-center flex-1">
          {navItems.map((item, index) => (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -20 }}
              animate={{ 
                opacity: 1, 
                x: 0,
                transition: { delay: index * 0.1, duration: 0.3 }
              }}
            >
              <Link 
                href={item.href} 
                onClick={() => setIsMobileOpen(false)}
                className="relative group/nav block"
              >
                <motion.div
                  className={`
                    relative flex items-center gap-3 p-3 rounded-xl transition-all duration-200
                    ${isActive(item.href) 
                      ? 'bg-primary/20 text-white shadow-[0_0_20px_rgba(59,130,246,0.15)]' 
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }
                  `}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {/* Left glowing accent bar */}
                  {isActive(item.href) && (
                    <motion.div
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full bg-primary shadow-[0_0_12px_rgba(59,130,246,0.8)]"
                      layoutId="activeBar"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  {isActive(item.href) && (
                    <motion.div
                      className="absolute inset-0 rounded-xl bg-primary/10 shadow-[0_0_25px_-5px_rgba(59,130,246,0.3)]"
                      layoutId="activeNav"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <item.icon 
                    size={22} 
                    className={`relative z-10 shrink-0 ${isActive(item.href) ? 'drop-shadow-[0_0_8px_rgba(59,130,246,0.6)]' : ''}`} 
                  />
                  
                  {/* Label - visible only on mobile */}
                  <span className="md:hidden text-sm font-medium relative z-10">{item.label}</span>
                </motion.div>
                
                {/* Tooltip on hover (desktop) */}
                <div className="hidden md:block absolute left-full top-1/2 -translate-y-1/2 ml-4 px-3 py-1.5 rounded-lg bg-[#0f0f1a] border border-white/20 text-[11px] text-white font-bold opacity-0 group-hover/nav:opacity-100 group-hover/nav:translate-x-1 transition-all duration-300 shadow-2xl z-50 pointer-events-none before:content-[''] before:absolute before:right-full before:top-1/2 before:-translate-y-1/2 before:border-8 before:border-transparent before:border-right-[#0f0f1a]">
                  {item.label}
                </div>
              </Link>
            </motion.div>
          ))}
          
          <motion.div 
            className="h-px w-8 bg-white/10 my-2"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.5 }}
          />
        </div>

        {/* Bottom Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col items-center w-full px-4"
        >
          <Link 
            href="/settings"
            onClick={() => setIsMobileOpen(false)}
            className="relative group/nav block w-full"
          >
            <motion.div
              className="p-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-colors mb-2 flex items-center justify-center md:justify-start gap-3"
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              transition={{ type: 'spring', stiffness: 400, damping: 17 }}
            >
              <Settings size={24} />
              <span className="md:hidden text-sm font-medium">Settings</span>
            </motion.div>
            <div className="hidden md:block absolute left-full top-1/2 -translate-y-1/2 ml-4 px-3 py-1.5 rounded-lg bg-[#0f0f1a] border border-white/20 text-[11px] text-white font-bold opacity-0 group-hover/nav:opacity-100 group-hover/nav:translate-x-1 transition-all duration-300 shadow-2xl z-50 pointer-events-none before:content-[''] before:absolute before:right-full before:top-1/2 before:-translate-y-1/2 before:border-8 before:border-transparent before:border-right-[#0f0f1a]">
              Settings
            </div>
          </Link>
        </motion.div>
      </motion.nav>
    </>
  );
};

export default Sidebar;
