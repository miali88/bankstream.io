import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useNavigate,
} from "@remix-run/react";
import { rootAuthLoader } from "@clerk/remix/ssr.server";
import { ClerkApp } from "@clerk/remix";
import type { LinksFunction, LoaderFunction } from "@remix-run/node";
import { useUser } from "@clerk/remix";

import "./tailwind.css";

if (!process.env.VITE_CLERK_PUBLISHABLE_KEY) {
  throw new Error("Missing Clerk Publishable Key");
}

export const links: LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export const loader: LoaderFunction = args => rootAuthLoader(args);

function AppLayout() {
  const { user } = useUser();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold">BankStream</span>
              </div>
            </div>
            <div className="flex items-center">
              {user ? (
                <button
                  onClick={() => navigate("/user-profile")}
                  className="text-gray-700 hover:text-gray-900"
                >
                  {user.firstName || user.username}
                </button>
              ) : (
                <button
                  onClick={() => navigate("/sign-in")}
                  className="text-gray-700 hover:text-gray-900"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full bg-gray-50">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body className="h-full">
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

function App() {
  return <AppLayout />;
}

export default ClerkApp(App, {
  publishableKey: process.env.VITE_CLERK_PUBLISHABLE_KEY
});
