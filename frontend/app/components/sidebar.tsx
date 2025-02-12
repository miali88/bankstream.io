import { Link, useLocation } from "@remix-run/react";
import { cn } from "../lib/utils";
import { BarChart3, Receipt, LogOut, BookOpen } from "lucide-react";
import { Button } from "./ui/button";

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
  return (
    <>
      <div className="p-4 font-semibold border-b flex justify-between items-center">
        <span>Bankstream</span>
        {/* <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={(e) => {
            e.preventDefault();
            console.log("JJAJ", theme);
            setTheme(theme === "dark" ? "light" : "dark");
          }}
          className="hover:bg-transparent"
        >
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button> */}
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
