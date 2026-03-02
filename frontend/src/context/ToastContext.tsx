'use client';

import React, { createContext, useContext, useCallback, ReactNode } from 'react';
import { Toaster, toast as sonnerToast } from 'sonner';

interface ToastContextType {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const success = useCallback((msg: string) => sonnerToast.success(msg), []);
  const error = useCallback((msg: string) => sonnerToast.error(msg), []);
  const info = useCallback((msg: string) => sonnerToast.info(msg), []);
  const warning = useCallback((msg: string) => sonnerToast.warning(msg), []);

  return (
    <ToastContext.Provider value={{ success, error, info, warning }}>
      {children}
      <Toaster 
        theme="dark" 
        position="bottom-right" 
        toastOptions={{
          style: {
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%)',
            backdropFilter: 'blur(40px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            color: 'white',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
          },
          className: 'rounded-2xl'
        }} 
      />
    </ToastContext.Provider>
  );
};
