'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Template {
  id: string;
  name: string;
  subject: string;
  body: string;
  lastUsed?: number;
}

interface TemplateContextType {
  templates: Template[];
  addTemplate: (template: Omit<Template, 'id'>) => void;
  updateTemplate: (id: string, template: Partial<Template>) => void;
  deleteTemplate: (id: string) => void;
}

const TemplateContext = createContext<TemplateContextType | undefined>(undefined);

export const TemplateProvider = ({ children }: { children: React.ReactNode }) => {
  const [templates, setTemplates] = useState<Template[]>([]);

  useEffect(() => {
    const initTemplates = async () => {
      const stored = localStorage.getItem('email_templates');
      if (stored) {
        setTemplates(JSON.parse(stored) as Template[]);
      } else {
        // Default Templates
        const defaults: Template[] = [
          {
              id: 'default-1',
              name: 'Quick Connect',
              subject: 'Quick question regarding your work at {{company}}',
              body: "Hi {{name}},\n\nI noticed your recent work at {{company}} and wanted to reach out.\n\nI'm curious about how you're handling [specific challenge].\n\nBest,\n[Your Name]"
          },
          {
              id: 'default-2',
              name: 'Partnership Inquiry',
              subject: 'Partnership opportunity: {{company}} x [My Company]',
              body: "Hi {{name}},\n\nI'm [Your Name] from [My Company]. We're helping companies like {{company}} scale their [specific area].\n\nWould you be open to a 10-min chat?\n\nBest,\n[Your Name]"
          }
        ];
        setTemplates(defaults);
        localStorage.setItem('email_templates', JSON.stringify(defaults));
      }
    };
    initTemplates();
  }, []);

  const save = (newTemplates: Template[]) => {
    setTemplates(newTemplates);
    localStorage.setItem('email_templates', JSON.stringify(newTemplates));
  };

  const addTemplate = (t: Omit<Template, 'id'>) => {
    const newTemplate = { ...t, id: crypto.randomUUID(), lastUsed: Date.now() };
    save([newTemplate, ...templates]);
  };

  const updateTemplate = (id: string, updates: Partial<Template>) => {
    save(templates.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const deleteTemplate = (id: string) => {
    save(templates.filter(t => t.id !== id));
  };

  return (
    <TemplateContext.Provider value={{ templates, addTemplate, updateTemplate, deleteTemplate }}>
      {children}
    </TemplateContext.Provider>
  );
};

export const useTemplates = () => {
  const context = useContext(TemplateContext);
  if (!context) throw new Error('useTemplates must be used within TemplateProvider');
  return context;
};
