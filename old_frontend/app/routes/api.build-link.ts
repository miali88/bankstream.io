import { json } from "@remix-run/node";
import type { ActionFunction } from "@remix-run/node";

export const action: ActionFunction = async ({ request }) => {
  const formData = await request.formData();
  const institution_id = formData.get("institution_id");

  const response = await fetch("http://localhost:8000/build_link", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ institution_id }),
  });
  
  const data = await response.json();
  return json(data);
}; 