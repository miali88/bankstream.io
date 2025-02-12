/// <reference types="@remix-run/dev" />
/// <reference types="@remix-run/node" />

declare module '@remix-run/node' {
  interface ProcessEnv {
    VITE_CLERK_PUBLISHABLE_KEY: string;
    VITE_CLERK_SECRET_KEY: string;
    VITE_API_URL: string;
  }
} 