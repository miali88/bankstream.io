import { type MetaFunction } from "@remix-run/node";
import { Link } from "@remix-run/react";
import { Button } from "~/components/ui/button";
import { UserButton } from "@clerk/remix";

export const meta: MetaFunction = () => {
  return [
    { title: "New Remix App" },
    { name: "description", content: "Welcome to Remix!" },
  ];
};

export default function Index() {
  return (
    <div className="flex flex-col h-screen">
      <nav className="border-b">
        <div className=" flex w-full justify-between h-14 items-center px-4">
          <div className="mr-4 font-semibold">Bankstream</div>
          <div className="flex items-center gap-2">
            <UserButton />
            <Button asChild variant="outline">
              <Link to="/sign-in">Sign In</Link>
            </Button>
            <Button asChild variant="default">
              <Link to="/dashboard/transactions">Dashboard</Link>
            </Button>
          </div>
        </div>
      </nav>
      <div className="flex-1 flex items-center justify-center">
        <h1 className="text-3xl font-bold">Welcome to Bankstream</h1>
      </div>
    </div>
  );
}
