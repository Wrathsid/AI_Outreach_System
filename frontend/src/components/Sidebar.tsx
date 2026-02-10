'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, Settings, Brain, Menu, X, Users, Mail, Search } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Sidebar = () => {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const [isMobile, setIsMobile] = useState(false);

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
    { href: '/drafts', icon: Mail, label: 'Drafts' },
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
          shadow-glass border-r-0
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
          <motion.div 
            className="bg-center bg-no-repeat bg-cover rounded-full size-12 shadow-lg ring-2 ring-white/10" 
            style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBXRt6dLsnIlX1FqjzEzocSMwA4U5jYadog5VnpuINqK2rcNy2lJyVmKHo-cSc7nOZEkRIWPFZP8btRf2iNM5eHJz5rvIsBx7V620ZutDXFBoJISXi4vx2GzPSHvRz7LXDpcs7RrfO4n-5eUoiFCl3awvnp731qmHDjJA671Z83FqNI7wavnAL_wqXyc3n6VyQd4HuGuws3BKB2wrzydcq8KouwQPiYXbXbbVTbDKOt-BB6OtqHMqTUuHFkLZq0ymACETLUYcxBrPXv")' }}
            whileHover={{ scale: 1.1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 17 }}
          />
          <motion.div 
            className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-[#1a1a2e] rounded-full"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
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
                className="relative"
              >
                <motion.div
                  className={`
                    ${isActive(item.href) 
                      ? 'bg-primary/20 text-white shadow-[0_0_20px_-5px_rgba(37,99,235,0.3)]' 
                      : 'text-white/40 hover:text-white hover:bg-white/5'
                    }
                  `}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {isActive(item.href) && (
                    <motion.div
                      className="absolute inset-0 rounded-xl bg-primary/20 shadow-[0_0_15px_-3px_rgba(25,25,230,0.4)]"
                      layoutId="activeNav"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  <item.icon size={24} className="relative z-10" />
                  <span className="md:hidden text-sm font-medium relative z-10">{item.label}</span>
                  <span className="hidden md:block absolute left-14 bg-black/80 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">{item.label}</span>
                </motion.div>
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
        >
          <Link 
            href="/settings"
            onClick={() => setIsMobileOpen(false)}
          >
            <motion.div
              className="p-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-colors mb-2 flex items-center gap-3"
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              transition={{ type: 'spring', stiffness: 400, damping: 17 }}
            >
              <Settings size={24} />
              <span className="md:hidden text-sm font-medium">Settings</span>
            </motion.div>
          </Link>
        </motion.div>
      </motion.nav>
    </>
  );
};

export default Sidebar;
