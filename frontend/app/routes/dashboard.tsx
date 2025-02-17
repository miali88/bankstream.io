import { Outlet, useLocation } from "@remix-run/react";
import { Menu } from "lucide-react";
import { Button } from "../components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "../components/ui/sheet";
import { useState } from "react";
import { SidebarContent } from "../components/sidebar";
import { getAuth } from "@clerk/remix/ssr.server";
import { redirect } from "@remix-run/node";
import type { LoaderFunction } from "@remix-run/node";
import { UserButton } from "@clerk/remix";

declare global {
  interface ImportMetaEnv {
    VITE_API_BASE_URL: string;
  }
}

export const ssr = false;

export const loader: LoaderFunction = async (args) => {
  const { userId } = await getAuth(args);
  if (!userId) {
    // return redirect("/sign-in");
  }
  return { ok: true };
};

// Add a loader to prevent indefinite loading

function Dashboard() {
  const location = useLocation();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      {/* Mobile Sidebar Trigger */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden absolute top-4 left-4"
          >
            <Menu className="h-6 w-6" />
          </Button>
        </SheetTrigger>

        {/* Mobile Sidebar Content */}
        <SheetContent side="left" className="w-64 p-0">
          <SidebarContent location={location} setOpen={setOpen} />
        </SheetContent>
      </Sheet>

      <div className="flex min-h-screen">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block w-64 border-r bg-background">
          <SidebarContent location={location} />
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-auto">
          {/* Add Topbar with UserButton */}
          <div className="border-b p-[13.8px] flex justify-end">
            <UserButton afterSignOutUrl="/sign-in" />
          </div>

          <div className="container p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
