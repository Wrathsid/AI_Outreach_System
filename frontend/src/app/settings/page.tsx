"use client";

import { useState, useEffect, useRef } from "react";
import { Camera, Trash2, Upload, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { api, API_BASE } from "@/lib/api";
import { useToast } from "@/context/ToastContext";

export default function SettingsPage() {
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Profile state
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Load settings
  useEffect(() => {
    (async () => {
      try {
        const settings = await api.getSettings();
        setFullName(settings.full_name || "");
        setCompany(settings.company || "");
        setRole(settings.role || "");
        if (settings.avatar_url) {
          const url = settings.avatar_url.startsWith("/")
            ? `${API_BASE}${settings.avatar_url}`
            : settings.avatar_url;
          setAvatarUrl(url);
        }
      } catch {
        // API unavailable — use empty defaults
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Get initials for fallback (filter empty parts to avoid crash on double spaces)
  const initials = fullName
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";

  // Save profile
  const saveProfile = async () => {
    setIsSaving(true);
    const success = await api.updateSettings({
      full_name: fullName,
      company,
      role,
      avatar_url: avatarUrl,
    });
    setIsSaving(false);
    if (success) {
      toast.success("Profile updated!");
    } else {
      toast.error("Failed to save profile");
    }
  };

  // Validate file
  const validateFile = (file: File): boolean => {
    const allowedTypes = ["image/jpeg", "image/png", "image/jpg"];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Only JPG and PNG files are allowed");
      return false;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 2MB");
      return false;
    }
    return true;
  };

  // Handle file select (from input or drop)
  const handleFile = async (file: File) => {
      if (!validateFile(file)) return;

      // Optimistic preview
      const localPreview = URL.createObjectURL(file);
      setPreviewUrl(localPreview);
      const previousAvatar = avatarUrl;

      setIsUploading(true);
      const result = await api.uploadAvatar(file);
      setIsUploading(false);

      if (result?.avatar_url) {
        const resolvedUrl = result.avatar_url.startsWith("/")
          ? `${API_BASE}${result.avatar_url}`
          : result.avatar_url;
        setAvatarUrl(resolvedUrl);
        setPreviewUrl(null);
        URL.revokeObjectURL(localPreview);
        toast.success("Avatar uploaded!");
      } else {
        // Rollback
        setPreviewUrl(null);
        setAvatarUrl(previousAvatar);
        URL.revokeObjectURL(localPreview);
        toast.error("Upload failed. Please try again.");
      }
    };

  // Remove avatar
  const handleRemoveAvatar = async () => {
    const previousAvatar = avatarUrl;
    setAvatarUrl(null);
    setPreviewUrl(null);

    const success = await api.removeAvatar();
    if (success) {
      toast.success("Avatar removed");
    } else {
      setAvatarUrl(previousAvatar);
      toast.error("Failed to remove avatar");
    }
  };

  // Drag handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const displayImage = previewUrl || avatarUrl;

  return (
    <main className="flex-1 flex flex-col h-full relative overflow-y-auto custom-scrollbar p-8">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/5 blur-[120px] animate-ambient-drift" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/5 blur-[100px] animate-ambient-drift-slow" />
      </div>

      <div className="z-10 w-full max-w-2xl mx-auto mt-16">
        <h1 className="text-2xl font-semibold text-white mb-2">Settings</h1>
        <p className="text-slate-400 text-sm mb-8">
          Configure your profile and outreach preferences.
        </p>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="animate-spin text-primary" size={24} />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Profile Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/3 border border-white/10 rounded-2xl p-6 md:p-8"
            >
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-6">
                Profile
              </h2>

              <div className="flex flex-col sm:flex-row items-center gap-8">
                {/* Avatar */}
                <div
                  className="relative group shrink-0"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div
                    className={`w-[120px] h-[120px] rounded-full overflow-hidden border-2 transition-all duration-300 flex items-center justify-center ${
                      isDragging
                        ? "border-primary shadow-[0_0_25px_-5px_rgba(0,113,227,0.5)] scale-105"
                        : "border-white/10 shadow-[0_0_20px_-5px_rgba(0,113,227,0.15)] hover:border-white/20"
                    } ${isUploading ? "animate-pulse" : ""}`}
                  >
                    {displayImage ? (
                      <img
                        src={displayImage}
                        alt="Avatar"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-linear-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                        <span className="text-3xl font-bold text-white/60">
                          {initials}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Green online indicator */}
                  <div className="absolute bottom-1 right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#0a0a0f] shadow-[0_0_8px_rgba(16,185,129,0.5)]" />

                  {/* Hover overlay */}
                  {!isUploading && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200 cursor-pointer"
                    >
                      <Camera size={24} className="text-white/80" />
                    </button>
                  )}

                  {isUploading && (
                    <div className="absolute inset-0 rounded-full bg-black/60 flex items-center justify-center">
                      <RefreshCw
                        size={20}
                        className="text-primary animate-spin"
                      />
                    </div>
                  )}
                </div>

                {/* Upload controls */}
                <div className="flex flex-col gap-3 items-center sm:items-start">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFile(file);
                      e.target.value = "";
                    }}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-sm text-slate-300 hover:text-white transition-all disabled:opacity-50"
                  >
                    <Upload size={14} />
                    Upload Photo
                  </button>
                  {displayImage && (
                    <button
                      onClick={handleRemoveAvatar}
                      disabled={isUploading}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-red-400/70 hover:text-red-400 hover:bg-red-500/5 transition-all disabled:opacity-50"
                    >
                      <Trash2 size={14} />
                      Remove
                    </button>
                  )}
                  <p className="text-slate-600 text-[11px]">
                    JPG or PNG • Max 2MB
                  </p>
                </div>
              </div>

              {/* Name / Company / Role fields */}
              <div className="mt-8 space-y-4">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Your name"
                    className="w-full bg-white/3 border border-white/10 focus:border-primary/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none transition-all"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1.5">
                      Company
                    </label>
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="Your company"
                      className="w-full bg-white/3 border border-white/10 focus:border-primary/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1.5">
                      Role
                    </label>
                    <input
                      type="text"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      placeholder="e.g. Software Engineer"
                      className="w-full bg-white/3 border border-white/10 focus:border-primary/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={saveProfile}
                    disabled={isSaving}
                    className="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-white text-sm font-medium transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {isSaving ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        Saving...
                      </>
                    ) : (
                      "Save Profile"
                    )}
                  </button>
                </div>
              </div>
            </motion.section>

            {/* Placeholder for future settings sections */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0, transition: { delay: 0.1 } }}
              className="bg-white/3 border border-white/10 rounded-2xl p-6"
            >
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
                Danger Zone
              </h2>
              <p className="text-slate-500 text-sm mb-4">
                Permanently delete your account and all associated data.
              </p>
              <button 
                onClick={async () => {
                  if (!confirm('Are you absolutely sure? This will permanently delete your account and all data. This cannot be undone.')) return;
                  if (!confirm('This is your final warning. Type "delete" in the next prompt to confirm.\n\nAre you sure you want to proceed?')) return;
                  try {
                    const success = await api.deleteAccount();
                    if (success) {
                      const supabase = (await import('@/lib/supabase')).createClient();
                      await supabase.auth.signOut();
                      window.location.href = '/login';
                    } else {
                      alert('Failed to delete account. Please try again.');
                    }
                  } catch {
                    alert('An error occurred. Please try again.');
                  }
                }}
                className="px-4 py-2 rounded-xl text-sm font-medium text-red-400 border border-red-500/20 hover:bg-red-500/10 transition-all"
              >
                Delete Account
              </button>
            </motion.section>
          </div>
        )}
      </div>
    </main>
  );
}