/* eslint-disable import/no-unresolved */
import { LoaderFunction, json } from "@remix-run/node";
import { getAuth } from "@clerk/remix/ssr.server";
import { downloadTransactionsCsv } from "~/api/transactions";

export const createAndClickDownloadableAnchorElement = (
  data: Blob | MediaSource,
  fileName: string
) => {
  const dataUrl = URL.createObjectURL(data);
  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.target = "_self";
  anchor.referrerPolicy = "no-referrer";
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(dataUrl);
};

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    throw new Error("Unauthorized");
  }

  const token = await getToken();
  const csvBlob = await downloadTransactionsCsv(token as string);

  return json({
    csvData: await csvBlob.text(),
    contentType: csvBlob.type,
  });
};
