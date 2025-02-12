import { SignIn } from "@clerk/remix";
import { useEffect } from "react";

// Enable client-side rendering and control hydration

// Explicitly disable server-side rendering
export const ssr = false;

// Add a loader to prevent indefinite loading
export function clientLoader() {
  console.log("HESTTTTESTTT");
  return { ok: true };
}

export default function SignInPage() {
  useEffect(() => {
    console.log("Client-side SignIn page mounted");
  }, []);

  return (
    <div className="relative min-h-screen bg-background">
      <div className="absolute top-4 left-4">
        {/* Logo can be added here */}
        <h1>TESTTT ME OIT</h1>
      </div>
      <div className="flex justify-center items-center min-h-screen">
        <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
      </div>
    </div>
  );
}
