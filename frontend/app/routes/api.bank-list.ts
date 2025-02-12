import { json } from "@remix-run/node";
import type { LoaderFunction } from "@remix-run/node";

export const loader: LoaderFunction = async () => {
  const response = await fetch("http://localhost:8000/bank_list");
  const data = await response.json();
  return json(data);
}; 