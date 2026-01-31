'use client';

import React from 'react';
import { Bell, Clock, ArrowRight, BookOpen, PlayCircle, Download } from 'lucide-react';

interface Resource {
  id: number;
  title: string;
  description: string;
  category: string;
  type: 'article' | 'video' | 'template';
  readTime?: string;
  featured?: boolean;
  image?: string;
  tags: string[];
  url: string;
  duration?: string;
  downloads?: string;
}

const resources: Resource[] = [
  {
    id: 1,
    title: 'The Ultimate Guide to Cold Emailing',
    description: 'A complete breakdown of cold email outreach covering structure, personalization, timing, and best practices for higher reply rates.',
    category: 'Strategy',
    type: 'article',
    readTime: '15 min read',
    featured: true,
    image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',
    tags: ['outreach', 'strategy'],
    url: 'https://medium.com/@Jus10McGill/the-complete-guide-to-cold-email-outreach-best-practices-2f93a269008'
  },
  {
    id: 2,
    title: '20 Cold Email Subject Lines That Actually Get Responses',
    description: 'A curated list of proven subject lines designed to improve open rates and spark real responses.',
    category: 'Strategy',
    type: 'article',
    readTime: '8 min read',
    image: 'https://images.unsplash.com/photo-1586769852044-692d6e3703f0?w=800',
    tags: ['subject-lines', 'copywriting'],
    url: 'https://www.brafton.com/blog/email-marketing/20-cold-email-subject-lines-that-actually-get-responses/'
  },
  {
    id: 3,
    title: 'The Complete Guide to Cold Email Marketing',
    description: 'An in-depth guide on building scalable cold email systems, from targeting and copywriting to optimization.',
    category: 'Guide',
    type: 'article',
    readTime: '12 min read',
    image: 'https://images.unsplash.com/photo-1555421689-d68471e189f2?w=800',
    tags: ['marketing', 'strategy', 'guide'],
    url: 'https://www.demandcurve.com/blog/cold-email-marketing'
  },
  {
    id: 4,
    title: 'Cold Email Follow-Up: When and How to Send It',
    description: 'Learn the ideal follow-up timing, messaging strategy, and cadence to increase replies without sounding spammy.',
    category: 'Strategy',
    type: 'article',
    readTime: '10 min read',
    image: 'https://images.unsplash.com/photo-1512428559087-560fa5ce7d02?w=800',
    tags: ['follow-up', 'strategy'],
    url: 'https://www.artisan.co/blog/cold-email-follow-up'
  },
];

export default function Resources() {
  const featuredResource = resources.find(r => r.featured);
  const regularResources = resources.filter(r => !r.featured);

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto relative bg-background-dark/50">
      {/* Search Header */}
      <header className="sticky top-0 z-50 glass-panel border-b-0 backdrop-blur-3xl bg-[#0F0F12]/80">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h2 className="text-white text-lg font-bold tracking-tight">Growth Hub</h2>
            <div className="flex items-center gap-4">
              <button className="relative text-white/70 hover:text-white transition-colors">
                <Bell size={20} />
                <span className="absolute top-0 right-0 size-2 bg-primary rounded-full ring-2 ring-[#111118]"></span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="grow">
        <div className="max-w-[960px] mx-auto px-4 py-12 md:py-16 flex flex-col gap-10">
          
          {/* Hero Section */}
          <div className="flex flex-col items-center text-center gap-6 animate-fade-in-up">
            <div className="flex flex-col gap-3 max-w-2xl">
              <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white drop-shadow-sm">
                Your Growth Resources
              </h1>
              <p className="text-[#9d9db8] text-lg font-light leading-relaxed">
                Curated guides, expert templates, and calm advice to help you connect and grow authentically.
              </p>
            </div>
          </div>
          {/* Featured Card */}
          {featuredResource && (
            <a 
              href={featuredResource.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full relative group cursor-pointer block"
            >
              <div className="absolute -inset-0.5 bg-linear-to-r from-primary/30 to-[#4c4cff]/30 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
              <div className="relative glass-panel rounded-2xl overflow-hidden md:flex md:h-[280px]">
                <div className="md:w-5/12 h-64 md:h-full relative overflow-hidden">
                  <div className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105" style={{ backgroundImage: `url("${featuredResource.image}")` }}></div>
                  <div className="absolute inset-0 bg-linear-to-t md:bg-linear-to-r from-black/80 via-black/20 to-transparent md:via-transparent"></div>
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 bg-primary/90 backdrop-blur-sm text-white text-xs font-bold rounded-full uppercase tracking-wider shadow-lg">Featured</span>
                  </div>
                </div>
                <div className="md:w-7/12 p-6 md:p-8 flex flex-col justify-center bg-[#15151b]/80 md:bg-transparent backdrop-blur-md md:backdrop-blur-none">
                  <div className="flex items-center gap-2 mb-3 text-[#9d9db8] text-sm">
                    <Clock size={16} />
                    <span>{featuredResource.readTime}</span>
                    <span className="mx-1">•</span>
                    <span>{featuredResource.category}</span>
                  </div>
                  <h3 className="text-2xl md:text-3xl font-bold text-white leading-tight mb-4 group-hover:text-primary/90 transition-colors">{featuredResource.title}</h3>
                  <p className="text-[#9d9db8] mb-6 line-clamp-2 leading-relaxed">{featuredResource.description}</p>
                  <div className="flex items-center">
                    <span className="text-white text-sm font-semibold group-hover:underline decoration-primary underline-offset-4">Read Guide</span>
                    <ArrowRight size={16} className="text-primary ml-1 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </a>
          )}

          {/* Content Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {regularResources.map((resource) => (
              <a 
                href={resource.url || '#'} 
                target="_blank" 
                rel="noopener noreferrer"
                key={resource.id} 
                className="glass-panel rounded-xl overflow-hidden group cursor-pointer flex flex-col h-full hover:-translate-y-1 transition-transform duration-300"
              >
                {resource.image && (
                  <div className="relative h-48 overflow-hidden">
                    <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url("${resource.image}")` }}></div>
                    {resource.type === 'video' && (
                      <>
                        <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center">
                            <PlayCircle size={32} className="text-white fill-white/20" />
                          </div>
                        </div>
                        <div className="absolute bottom-3 right-3 bg-black/70 px-2 py-0.5 rounded text-[10px] font-bold text-white">{resource.duration}</div>
                      </>
                    )}
                    <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm p-1.5 rounded-lg text-white">
                      {resource.type === 'video' ? <PlayCircle size={16} /> : <BookOpen size={16} />}
                    </div>
                  </div>
                )}
                {resource.type === 'template' && (
                  <div className="relative h-48 overflow-hidden bg-[#16161e] flex items-center justify-center border-l-4 border-l-primary/50">
                    <div className="bg-primary/20 backdrop-blur-sm rounded-full p-4 border border-primary/30 group-hover:scale-110 transition-transform">
                      <Download size={24} className="text-primary" />
                    </div>
                  </div>
                )}
                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      resource.type === 'template' ? 'text-blue-400 bg-blue-400/10' :
                      resource.type === 'video' ? 'text-emerald-400 bg-emerald-400/10' :
                      'text-primary bg-primary/10'
                    }`}>{resource.category}</span>
                    {resource.readTime && <span className="text-xs text-[#6b6b7f]">{resource.readTime}</span>}
                    {resource.downloads && <span className="text-xs text-[#6b6b7f]">{resource.downloads} downloads</span>}
                  </div>
                  <h4 className="text-lg font-bold text-white mb-2 leading-tight">{resource.title}</h4>
                  <p className="text-[#9d9db8] text-sm line-clamp-2 mb-4 flex-1">{resource.description}</p>
                  {resource.type !== 'template' && (
                    <div className="mt-auto pt-4 border-t border-white/5 flex items-center justify-between">
                      <div className="flex -space-x-2">
                        <div className="w-6 h-6 rounded-full bg-gray-600 border border-[#1c1c26]"></div>
                        <div className="w-6 h-6 rounded-full bg-gray-500 border border-[#1c1c26]"></div>
                      </div>
                      <span className="text-xs text-[#6b6b7f] group-hover:text-white transition-colors">Read Article</span>
                    </div>
                  )}
                </div>
              </a>
            ))}
          </div>



          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-[#6b6b7f]">
            <p>© 2024 Personal Growth Hub. All rights reserved.</p>
            <div className="flex gap-6">
              <a className="hover:text-white transition-colors" href="#">Community</a>
              <a className="hover:text-white transition-colors" href="#">Contact Support</a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
