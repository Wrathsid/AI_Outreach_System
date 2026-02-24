"use client";

export default function SettingsPage() {
  return (
    <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
      <div className="z-10 w-full max-w-2xl mx-auto mt-16">
        <h1 className="text-2xl font-semibold text-white mb-2">Settings</h1>
        <p className="text-slate-400 text-sm mb-8">
          Configure your outreach preferences and API keys.
        </p>
        <div className="bg-white/5 border border-white/10 rounded-xl p-6">
          <p className="text-slate-500 text-sm">Settings page coming soon.</p>
        </div>
      </div>
    </main>
  );
}