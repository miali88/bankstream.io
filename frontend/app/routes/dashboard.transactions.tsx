/* eslint-disable import/no-unresolved */
import { columns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { mockTransactions } from "../components/transactions/mock-data";
import { Input } from "~/components/ui/input";
import { AddAccountDialog } from "~/components/transactions/add-account-dialog";
import type { LoaderFunction, ActionFunction } from "@remix-run/node";
import { getBankList, getBuildLink } from "~/api/transactions";

interface CountryData {
  cca2: string;
  name: { common: string };
  flag: string;
}

const ALLOWED_COUNTRIES: Record<string, string> = {
  AU: "Australia",
  AT: "Austria",
  BE: "Belgium",
  BG: "Bulgaria",
  CA: "Canada",
  HR: "Croatia",
  CY: "Cyprus",
  CZ: "Czech Republic",
  DK: "Denmark",
  FI: "Finland",
  FR: "France",
  DE: "Germany",
  HU: "Hungary",
  IT: "Italy",
  LU: "Luxembourg",
  MT: "Malta",
  NL: "Netherlands",
  NZ: "New Zealand",
  NO: "Norway",
  PL: "Poland",
  PT: "Portugal",
  IE: "Republic of Ireland",
  RO: "Romania",
  SK: "Slovakia",
  SI: "Slovenia",
  ZA: "South Africa",
  ES: "Spain",
  SE: "Sweden",
  CH: "Switzerland",
  GB: "United Kingdom",
  US: "United States",
};

export const clientLoader: LoaderFunction = async () => {
  // Fetch countries data from an API
  const response = await fetch("https://restcountries.com/v3.1/all");
  const data = await response.json();

  // Filter and transform the data to match our needs
  const countries = data
    .filter((country: CountryData) => ALLOWED_COUNTRIES[country.cca2])
    .map((country: CountryData) => ({
      code: country.cca2,
      name: ALLOWED_COUNTRIES[country.cca2], // Use our predefined names
      flag: country.flag,
    }))
    .sort((a: { name: string }, b: { name: string }) =>
      a.name.localeCompare(b.name)
    ); // Sort alphabetically by name

  return { countries };
};

export const action: ActionFunction = async ({ request }) => {
  const formData = await request.formData();
  const country = formData.get("country") as string;
  const bankId = formData.get("bankId") as string;

  try {
    if (country) {
      const bankList = await getBankList(country);
      return { bankList };
    }

    if (bankId) {
      const { link } = await getBuildLink(bankId);
      return { link };
    }
  } catch (error) {
    console.error("Error:", error);
    throw new Error("Failed to process request");
  }
};

export default function Transactions() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Transactions</h2>
      <div className="rounded-lg shadow p-4">
        <div className="flex items-center justify-between py-4">
          <Input placeholder="Search all columns..." className="max-w-sm" />
          <AddAccountDialog />
        </div>
        <DataTable columns={columns} data={mockTransactions} />
      </div>
    </div>
  );
}
