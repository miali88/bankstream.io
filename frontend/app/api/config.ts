export const buildUrl = (
  pathname: string,
  searchParams: string | URLSearchParams = ""
) => {
  const url = new URL(import.meta.env.VITE_API_BASE_URL as string);

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
