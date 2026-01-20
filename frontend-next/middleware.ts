import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('token')?.value;
    const { pathname } = request.nextUrl;

    // Paths that require authentication
    const protectedPaths = ['/', '/meetings', '/calendar'];

    // Check if current path is protected
    const isProtected = protectedPaths.some(path =>
        pathname === path || pathname.startsWith(`${path}/`)
    );

    // If trying to access protected route without token, redirect to login
    if (isProtected && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // If logged in and trying to access login, redirect to dashboard
    if (pathname === '/login' && token) {
        return NextResponse.redirect(new URL('/', request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
};
