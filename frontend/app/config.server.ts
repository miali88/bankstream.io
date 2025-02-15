// Server-side configuration
const getApiBaseUrl = () => {
  // Explicitly check for server-side environment variables
  const serverUrl = process.env.API_BASE_URL;
  if (serverUrl) {
    console.log('Using server API URL:', serverUrl);
    return serverUrl;
  }

  // Fallback to development URL
  const defaultUrl = 'http://localhost:8001/api/v1';
  console.log('Using default API URL:', defaultUrl);
  return defaultUrl;
};

export const config = {
  apiBaseUrl: getApiBaseUrl(),
  clerkPublishableKey: process.env.CLERK_PUBLISHABLE_KEY,
  clerkSecretKey: process.env.CLERK_SECRET_KEY,
}; 