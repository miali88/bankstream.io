import type { LinksFunction } from "@remix-run/node";
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "@remix-run/react";
import "./tailwind.css";
import { ThemeProvider } from "./components/theme-provider";

export const links: LinksFunction = () => [
  { rel: "stylesheet", href: "/tailwind.css" }
];

export default function App() {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider defaultTheme="dark" storageKey="app-theme">
          <Outlet />
        </ThemeProvider>
        <ScrollRestoration />
        <Scripts />
        <LiveReload />
      </body>
    </html>
  );
}
