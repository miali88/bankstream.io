import { Link, useLocation } from "@remix-run/react";
import { cn } from "../lib/utils";
import { BarChart3, Receipt, LogOut, BookOpen, Link2 } from "lucide-react";
import { Button } from "./ui/button";
import { buildUrl } from "../api/config";
import { useAuth } from "@clerk/remix";

const sidebarItems = [
  {
    title: "Transactions",
    icon: Receipt,
    href: "/dashboard/transactions",
  },
  {
    title: "Hub",
    icon: BarChart3,
    href: "/dashboard/hub",
  },
  {
    title: "Chart of Accounts",
    icon: BookOpen,
    href: "/dashboard/chart-of-accounts",
  },
];

interface SidebarContentProps {
  location: ReturnType<typeof useLocation>;
  setOpen?: (open: boolean) => void;
}

export function SidebarContent({ location, setOpen }: SidebarContentProps) {
  const { getToken } = useAuth();
  
  const handleXeroConnect = async () => {
    const token = await getToken();
    const state = JSON.stringify({ 
      clerk_token: token,
      xero_state: crypto.randomUUID()
    });
    
    // Create URL object to properly handle query parameters
    const url = new URL(buildUrl('xero/login'));
    url.searchParams.append('state', state);
    window.location.href = url.toString();
  };

  return (
    <>
      <div className="p-4 font-semibold border-b flex justify-between items-center">
        <span>Bankstream</span>
      </div>
      <nav className="space-y-1 p-2 flex flex-col h-full">
        <div className="flex-1">
          {sidebarItems.map((item) => (
            <Button
              key={item.href}
              variant={location.pathname === item.href ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start gap-2",
                location.pathname === item.href && "bg-secondary"
              )}
              onClick={() => setOpen?.(false)}
              asChild
            >
              <Link prefetch="intent" to={item.href}>
                <item.icon className="h-4 w-4" />
                {item.title}
              </Link>
            </Button>
          ))}
          <Button
            variant="ghost"
            className="w-full justify-start gap-2"
            onClick={handleXeroConnect}
          >
            <Link2 className="h-4 w-4" />
            Connect to Xero
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-2"
            onClick={() => (window.location.href = "/")}
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </nav>
    </>
  );
}
