export const buildUrl = (
  pathname: string,
  searchParams: string | URLSearchParams = ""
) => {
  // Handle both server-side and client-side environment
  const baseUrl = typeof process !== 'undefined' && process.env.API_BASE_URL
    ? process.env.API_BASE_URL
    : import.meta.env.VITE_API_BASE_URL;

  // Force IPv4 by using explicit IP if localhost
  const url = new URL(baseUrl as string);
  if (url.hostname === 'localhost' || url.hostname === '::1') {
    url.hostname = '127.0.0.1';
  }

  // Ensure there is no double slash when appending the pathname
  url.pathname = `${url.pathname.replace(/\/$/, "")}/${pathname.replace(
    /^\//,
    ""
  )}`;
  url.search = searchParams.toString();

  return url.href;
};

export type ApiResponse<T> = {
  status: number;
  message: string;
  options: Record<string, { length?: number }>;
  data: T[];
};
