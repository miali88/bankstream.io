import { buildUrl } from "./config";

export async function getBankList(country: string) {
  const searchParams = new URLSearchParams({ country });
  const url = buildUrl("gocardless/bank_list", searchParams);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || `HTTP error! status: ${response.status}`
    );
  }

  return await response.json();
}

export async function getBuildLink(institutionId: string) {
  const searchParams = new URLSearchParams({ institution_id: institutionId });
  const url = buildUrl("gocardless/build_link", searchParams);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
