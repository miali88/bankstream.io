/* eslint-disable import/no-unresolved */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "~/components/ui/dialog";
import { Button } from "~/components/ui/button";
import {
  Form,
  useLoaderData,
  useNavigation,
  useActionData,
  useSubmit,
} from "@remix-run/react";
import { useState, useEffect } from "react";
import { Spinner } from "~/components/ui/spinner";

import { Monitor, Smartphone } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { BankLinkSSEListener } from "./bank-link-sse-listener";

interface CountryOption {
  code: string;
  name: string;
  flag: string;
}

interface BankInfo {
  id: string;
  name: string;
  transaction_total_days: string;
  countries: string[];
  logo: string;
}

export function AddAccountDialog() {
  const { countries } = useLoaderData<{ 
    countries: CountryOption[];
    transactions: any[];
    page: number;
    page_size: number;
    total_pages: number;
    total_count: number;
  }>();
  const actionData = useActionData<{ bankList?: BankInfo[]; link?: string; ref?: string }>();
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedBank, setSelectedBank] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [step, setStep] = useState<"country" | "banks" | "link">("country");
  const [showQR, setShowQR] = useState(false);
  const [currentRef, setCurrentRef] = useState<string>("");
  const navigation = useNavigation();
  const submit = useSubmit();

  const resetStates = () => {
    setSelectedCountry("");
    setSelectedBank("");
    setSearchTerm("");
    setStep("country");
    setShowQR(false);
    setCurrentRef("");
  };

  const handleNext = () => {
    const formData = new FormData();
    formData.append("country", selectedCountry);
    submit(formData, { method: "post" });
    setStep("banks");
  };

  const handleGetLink = () => {
    const selectedBankInfo = bankList.find(bank => bank.id === selectedBank);
    if (!selectedBankInfo) return;
    
    const formData = new FormData();
    formData.append("bankId", selectedBank);
    formData.append("transactionTotalDays", selectedBankInfo.transaction_total_days);
    submit(formData, { method: "post" });
    setStep("link");
  };

  const isLoading = navigation.state === "submitting";
  const bankList = actionData?.bankList || [];
  const link = actionData?.link;
  const ref = actionData?.ref;

  useEffect(() => {
    if (ref) {
      setCurrentRef(ref);
    }
  }, [ref]);

  const filteredBanks = bankList.filter((bank) =>
    bank.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Dialog onOpenChange={(open) => !open && resetStates()}>
      <DialogTrigger asChild>
        <Button>Add bank link</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] sm:max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>Add Bank Account</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Spinner className="h-8 w-8" />
          </div>
        ) : (
          <Form method="post" className="space-y-6">
            {step === "country" ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="country-list" className="text-sm font-medium">
                    Select Country
                  </label>
                  <div
                    id="country-list"
                    className="border rounded-md p-4 max-h-[300px] overflow-y-auto space-y-2"
                  >
                    {countries.map((country) => (
                      <div
                        key={country.code}
                        className="flex items-center space-x-2"
                      >
                        <input
                          type="radio"
                          id={country.code}
                          name="country"
                          value={country.code}
                          checked={selectedCountry === country.code}
                          onChange={(e) => setSelectedCountry(e.target.value)}
                          className="w-4 h-4"
                        />
                        <label
                          htmlFor={country.code}
                          className="flex items-center gap-2 text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          <img
                            src={`https://flagcdn.com/24x18/${country.code.toLowerCase()}.png`}
                            alt={`${country.name} flag`}
                            className="w-6 h-4 object-cover rounded"
                          />
                          <span className="text-muted-foreground">
                            {country.code}
                          </span>
                          <span>{country.name}</span>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                <Button
                  type="button"
                  disabled={!selectedCountry}
                  onClick={handleNext}
                  className="w-full"
                >
                  Next
                </Button>
              </div>
            ) : step === "banks" ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="bank-list" className="text-sm font-medium">
                    Select Bank
                  </label>
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md text-sm"
                  />
                  <div
                    id="bank-list"
                    className="border rounded-md p-4 max-h-[400px] overflow-y-auto space-y-4"
                  >
                    {filteredBanks.map((bank) => (
                      <div
                        key={bank.id}
                        className="flex items-center space-x-3"
                      >
                        <input
                          type="radio"
                          id={bank.id}
                          name="bank"
                          value={bank.id}
                          checked={selectedBank === bank.id}
                          onChange={(e) => setSelectedBank(e.target.value)}
                          className="w-4 h-4"
                        />
                        <label
                          htmlFor={bank.id}
                          className="flex items-center gap-3 text-sm leading-none"
                        >
                          <img
                            src={bank.logo}
                            alt={bank.name}
                            className="w-8 h-8 object-contain"
                          />
                          <div className="space-y-1">
                            <p className="font-medium">{bank.name}</p>
                            <p className="text-sm text-muted-foreground">
                              Available transaction history:{" "}
                              {bank.transaction_total_days} days
                            </p>
                          </div>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep("country")}
                    className="w-full"
                  >
                    Back
                  </Button>
                  <Button
                    type="button"
                    className="w-full"
                    disabled={!selectedBank || isLoading}
                    onClick={handleGetLink}
                  >
                    {isLoading ? "Loading..." : "Get Link"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="space-y-4">
                  {!showQR ? (
                    <>
                      <BankLinkSSEListener referenceId={currentRef} />
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-center">
                          Choose how to login
                        </h3>
                        <div className="flex justify-center gap-8">
                          <Button
                            type="button"
                            onClick={() => window.open(link, "_blank")}
                            className="flex flex-col items-center gap-3 p-8"
                          >
                            <Monitor className="h-12 w-12" />
                            <span>Online Banking</span>
                          </Button>
                          <Button
                            type="button"
                            onClick={() => setShowQR(true)}
                            className="flex flex-col items-center gap-3 p-8"
                          >
                            <Smartphone className="h-12 w-12" />
                            <span>Mobile Banking</span>
                          </Button>
                        </div>
                      </div>
                      <div className="rounded-lg border p-3">
                        <p className="text-sm font-medium">Shareable link:</p>
                        <p className="mt-1 break-all text-xs text-muted-foreground">
                          {link}
                        </p>
                      </div>
                    </>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex justify-center p-4">
                        <QRCodeSVG
                          value={link || ""}
                          size={200}
                          level="H"
                          includeMargin
                        />
                      </div>
                      <p className="text-center text-sm text-muted-foreground">
                        Scan this QR code with your phone&apos;s camera
                      </p>
                    </div>
                  )}
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    if (showQR) {
                      setShowQR(false);
                    } else {
                      setStep("banks");
                    }
                  }}
                  className="w-full"
                >
                  Back
                </Button>
              </div>
            )}
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
