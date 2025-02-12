import { Outlet, useLocation } from "@remix-run/react";
import { Menu } from "lucide-react";
import { Button } from "../components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "../components/ui/sheet";
import { useState } from "react";
import { SidebarContent } from "../components/sidebar";

export const ssr = false;

// Add a loader to prevent indefinite loading
export function clientLoader() {
  return { ok: true };
}

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
          <div className="container p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
