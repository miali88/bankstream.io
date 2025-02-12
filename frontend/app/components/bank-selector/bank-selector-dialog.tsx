import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { ScrollArea } from "../ui/scroll-area";
import { useFetcher } from "@remix-run/react";

interface Bank {
  id: string;
  name: string;
  logo: string;
  countries: string[];
}

interface BankListResponse extends Array<Bank> {}
interface BuildLinkResponse {
  link: string;
}

export function BankSelectorDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const banksFetcher = useFetcher<BankListResponse>();
  const linkFetcher = useFetcher<BuildLinkResponse>();

  // Fetch banks when dialog opens
  useEffect(() => {
    if (isOpen) {
      banksFetcher.load("/api/bank-list");
    }
  }, [isOpen]);

  // Log fetcher states for debugging
  console.log("Banks Fetcher state:", {
    state: banksFetcher.state,
    data: banksFetcher.data,
  });
  console.log("Link Fetcher state:", {
    state: linkFetcher.state,
    data: linkFetcher.data,
  });

  const banks = (banksFetcher.data || []) as Bank[];
  const countries = Array.from(new Set(banks.flatMap((bank: Bank) => bank.countries))).sort();

  const filteredBanks = banks.filter((bank: Bank) => {
    const matchesCountry = selectedCountry === "all" || bank.countries.includes(selectedCountry);
    const matchesSearch = !searchTerm || 
      bank.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCountry && matchesSearch;
  });

  const handleBankSelect = (bank: Bank) => {
    linkFetcher.submit(
      { institution_id: bank.id },
      { method: "post", action: "/api/build-link" }
    );
  };

  // Handle link response
  useEffect(() => {
    if (linkFetcher.data?.link) {
      window.open(linkFetcher.data.link, "_blank");
      setIsOpen(false);
    }
  }, [linkFetcher.data]);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Add Accounts</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Select Your Bank</DialogTitle>
          <DialogDescription>
            Choose your bank to securely connect your account
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <Select
              value={selectedCountry}
              onValueChange={setSelectedCountry}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                {countries.map((country) => (
                  <SelectItem key={country} value={country}>
                    {country}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input
              placeholder="Search banks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <ScrollArea className="h-[400px] rounded-md border p-4">
            {banksFetcher.state === "loading" ? (
              <div className="flex items-center justify-center h-full">
                <p>Loading banks...</p>
              </div>
            ) : banks.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p>No banks found</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {filteredBanks.map((bank: Bank) => (
                  <Button
                    key={bank.id}
                    variant="outline"
                    className="flex items-center gap-2 p-4"
                    onClick={() => handleBankSelect(bank)}
                  >
                    <img 
                      src={bank.logo} 
                      alt={bank.name} 
                      className="h-8 w-8 object-contain"
                    />
                    <span className="text-sm">{bank.name}</span>
                  </Button>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
} 