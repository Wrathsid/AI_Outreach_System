
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  // BYPASS AUTHENTICATION for local dev/rate limit issues
  // Explicitly allow everything and redirect root to /search

  const path = request.nextUrl.pathname;
  
  if (path === '/') {
      return NextResponse.next();
  }
  
  // If trying to access login/signup, just go to app
  if (path === '/login' || path === '/signup') {
      return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next({
    request: {
      headers: request.headers,
    },
  });
}

export async function middleware(request: NextRequest) {
  return await updateSession(request)
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
