"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // 1. Check if user is authenticated
    const isAuthenticated = localStorage.getItem("isAuthenticated") === "true";
    
    // 2. Define public paths
    const publicPaths = ["/login", "/signup"];
    const isPublicPath = publicPaths.includes(pathname);

    let nextAuthorized = false;

    if (!isAuthenticated && !isPublicPath) {
      // If not logged in and trying to access private route -> Login
      nextAuthorized = false;
      if (pathname !== "/login") {
        router.push("/login"); 
      }
    } else if (isAuthenticated && isPublicPath) {
      // If logged in and trying to access login -> Dashboard
      nextAuthorized = true;
      router.push("/");
    } else {
      // Otherwise, allow access
      nextAuthorized = true;
    }
    
    // Wrap in requestAnimationFrame to avoid "cascading render" lint error
    // by making the state updates asynchronous.
    requestAnimationFrame(() => {
      setAuthorized(nextAuthorized);
      setIsLoaded(true);
    });
  }, [pathname, router]);

  // Prevent flashing of protected content and blank screen on initial mount
  if (!isLoaded) {
      return <div className="h-screen w-screen bg-black flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>;
  }

  if (!authorized && !["/login", "/signup"].includes(pathname)) {
      return null; 
  }

  return <>{children}</>;
}
