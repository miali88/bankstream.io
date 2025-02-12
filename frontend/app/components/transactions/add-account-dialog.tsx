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
import { useState } from "react";
import { Spinner } from "~/components/ui/spinner";

import { Monitor, Smartphone } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

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
  const { countries } = useLoaderData<{ countries: CountryOption[] }>();
  const actionData = useActionData<{ bankList?: BankInfo[]; link?: string }>();
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedBank, setSelectedBank] = useState<string>("");
  const [step, setStep] = useState<"country" | "banks" | "link">("country");
  const navigation = useNavigation();
  const submit = useSubmit();
  const [showQR, setShowQR] = useState(false);

  const resetStates = () => {
    setSelectedCountry("");
    setSelectedBank("");
    setStep("country");
    setShowQR(false);
  };

  const handleNext = () => {
    const formData = new FormData();
    formData.append("country", selectedCountry);
    submit(formData, { method: "post" });
    setStep("banks");
  };

  const handleGetLink = () => {
    const formData = new FormData();
    formData.append("bankId", selectedBank);
    submit(formData, { method: "post" });
    setStep("link");
  };

  const isLoading = navigation.state === "submitting";
  const bankList = actionData?.bankList || [];
  const link = actionData?.link;

  return (
    <Dialog onOpenChange={(open) => !open && resetStates()}>
      <DialogTrigger asChild>
        <Button>Add bank link</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
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
                  <div
                    id="bank-list"
                    className="border rounded-md p-4 max-h-[300px] overflow-y-auto space-y-4"
                  >
                    {bankList.map((bank) => (
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
                      <div className="flex justify-center gap-8">
                        <Button
                          type="button"
                          onClick={() => window.open(link, "_blank")}
                          className="flex flex-col items-center gap-3 p-8"
                        >
                          <Monitor className="h-12 w-12" />
                          <span>Open in Browser</span>
                        </Button>
                        <Button
                          type="button"
                          onClick={() => setShowQR(true)}
                          className="flex flex-col items-center gap-3 p-8"
                        >
                          <Smartphone className="h-12 w-12" />
                          <span>Open on Phone</span>
                        </Button>
                      </div>
                      <div className="rounded-lg border p-3">
                        <p className="text-sm font-medium">Link:</p>
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
