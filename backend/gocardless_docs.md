Quickstart Guide
This document explains how to jump-start your integration with the Bank Account Data API. For more detailed information on endpoint input parameters and response details, refer to section Endpoints.

If you are using Postman, you can follow these instructions on how to import Bank Account Data API schema.

## Step 1: Get Access Token
First, you'll need to get your user secret from GoCardless's Bank Account Data portal in section User Secrets. Use those secrets to create an access token (referenced as ACCESS_TOKEN in the following steps).

curl -X POST "https://bankaccountdata.gocardless.com/api/v2/token/new/" \
  -H "accept: application/json" \
  -H  "Content-Type: application/json" \
  -d "{\"secret_id\":\"string\", \"secret_key\":\"string\"}"

Copy
Response:

{  
  "access": "string",
  "access_expires": 86400,  
  "refresh": "string",  
  "refresh_expires": 2592000 
 }

Copy
## Step 2: Choose a Bank
Use institutions endpoint to get a list of all available financial institutions in a given country. You will need to provide a two-letter country code (ISO 3166). ID for the chosen bank will be used in the following steps (referenced as institution_id). Use SANDBOXFINANCE_SFIN0000 as institution_id if you wish to try out the Quickstart with the mock-up institution (see Sandbox).

See also the guide on how to build an end user interface for selecting a bank.

curl -X GET "https://bankaccountdata.gocardless.com/api/v2/institutions/?country=gb" \
  -H  "accept: application/json" \
  -H  "Authorization: Bearer ACCESS_TOKEN"

Copy
Response:

[
   {
      "id":"ABNAMRO_ABNAGB2LXXX",
      "name":"ABN AMRO Bank Commercial",
      "bic":"ABNAGB2LXXX",
      "transaction_total_days":"540",
      "countries":[
         "GB"
      ],
      "logo":"https://cdn-logos.gocardless.com/ais/ABNAMRO_FTSBDEFAXXX.png",
      "max_access_valid_for_days": "180"
   },
   {
      "..."
   },
   {
      "id":"REVOLUT_REVOGB21",
      "name":"Revolut",
      "bic":"REVOGB21",
      "transaction_total_days":"730",
      "countries":[
         "GB"
      ],
      "logo":"https://cdn-logos.gocardless.com/ais/REVOLUT_REVOGB21.png",
      "max_access_valid_for_days": "90"
   }
]

Copy
## Step 3: Create an end user agreement
NB! Use this step only if you want to specify other than default end user agreement terms: 90 days of transaction history, 90 days of account access period and full scope of information (details, balances, transactions). If no custom end user agreement is created, default terms will be applied.

You need to create an agreement and pass:

institution_id from Step 2.
And optionally:

max_historical_days as the length of the transaction history to be retrieved;
access_valid_for_days as the length of days while the access to account is valid;
access_scope for the scope of information.
curl -X POST "https://bankaccountdata.gocardless.com/api/v2/agreements/enduser/" \
  -H  "accept: application/json" \
  -H  "Content-Type: application/json" \
  -H  "Authorization: Bearer ACCESS_TOKEN" \
  -d "{\"institution_id\": \"REVOLUT_REVOGB21\",
       \"max_historical_days\": \"180\",
       \"access_valid_for_days\": \"30\",
       \"access_scope\": [\"balances\", \"details\", \"transactions\"] }"

Copy
Response:

{
   "id":"2dea1b84-97b0-4cb4-8805-302c227587c8",
   "created":"2021-10-25T16:41:09.753Z",
   "max_historical_days":180,
   "access_valid_for_days":30,
   "access_scope":[
      "balances",
      "details",
      "transactions"
   ],
   "accepted":"",
   "institution_id":"REVOLUT_REVOGB21"
}

Copy
## Step 4: Build a Link
You need to create a requisition, which is a collection of inputs for creating links and retrieving accounts. For requisition API requests you will need to provide:

institution_id from Step 2;
redirect URL where the end user will be redirected after finishing authentication in financial institution;
And optionally:

reference as a unique ID defined by you for internal referencing;
agreement as end user agreement ID from Step 3;
user_language to enforce a language for all end user steps hosted by GoCardless passed as a two-letter country code (ISO 639-1). If user_language is not defined a language set in browser will be used to determine language.
curl -X POST "https://bankaccountdata.gocardless.com/api/v2/requisitions/" \
  -H  "accept: application/json" -H  "Content-Type: application/json" \
  -H  "Authorization: Bearer ACCESS_TOKEN" \
  -d "{\"redirect\": \"http://www.yourwebpage.com\",
       \"institution_id\": \"REVOLUT_REVOGB21\",
       \"reference\": \"124151\",
       \"agreement\": \"2dea1b84-97b0-4cb4-8805-302c227587c8\",
       \"user_language\":\"EN\" }"

Copy
Response:

{
   "id":"8126e9fb-93c9-4228-937c-68f0383c2df7",
   "redirect":"http://www.yourwebpage.com",
   "status":{
      "short":"CR",
      "long":"CREATED",
      "description":"Requisition has been succesfully created"
   },
   "agreement":"2dea1b84-97b0-4cb4-8805-302c227587c8",
   "accounts":[

   ],
   "reference":"124151",
   "user_language":"EN",
   "link":"https://ob.gocardless.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/{$INSTITUTION_ID}"
}

Copy
Follow the link to start the end-user authentication process with the financial institution. Save the requisition ID (id in the response). You will later need it to retrieve the list of end-user accounts.

## Step 5: List accounts
Once the user is redirected back to the link provided in Step 4, the user's bank accounts can be listed. Pass the requisition ID to view the accounts.

curl -X GET "https://bankaccountdata.gocardless.com/api/v2/requisitions/8126e9fb-93c9-4228-937c-68f0383c2df7/" \
  -H  "accept: application/json" \
  -H  "Authorization: Bearer ACCESS_TOKEN" 

Copy
Response:

{
   "id":"8126e9fb-93c9-4228-937c-68f0383c2df7",
   "status":"LN",
   "agreements":"2dea1b84-97b0-4cb4-8805-302c227587c8",
   "accounts":[
      "065da497-e6af-4950-88ed-2edbc0577d20",
      "bc6d7bbb-a7d8-487e-876e-a887dcfeea3d"
   ],
   "reference":"124151"
}

Copy
## Step 6: Access account details, balances and transactions
There are three separate endpoints for accessing account details, balances, and transactions. See account endpoints to view respective endpoints.

In this quickstart, we will showcase the transactions' endpoint, where you need to pass the account ID (see “accounts” from the output of Step 5) to access transaction information. You will need to query each account separately.

curl -X GET "https://bankaccountdata.gocardless.com/api/v2/accounts/065da497-e6af-4950-88ed-2edbc0577d20/transactions/" \
  -H  "accept: application/json" \
  -H  "Authorization: Bearer ACCESS_TOKEN"

Copy
Response:

{
   "transactions":{
      "booked":[
         {
            "transactionId":"2020103000624289-1",
            "debtorName":"MON MOTHMA",
            "debtorAccount":{
               "iban":"GL53SAFI055151515"
            },
            "transactionAmount":{
               "currency":"EUR",
               "amount":"45.00"
            },
            "bookingDate":"2020-10-30",
            "valueDate":"2020-10-30",
            "remittanceInformationUnstructured":"For the support of Restoration of the Republic foundation"
         },
         {
            "transactionId":"2020111101899195-1",
            "transactionAmount":{
               "currency":"EUR",
               "amount":"-15.00"
            },
            "bankTransactionCode":"PMNT",
            "bookingDate":"2020-11-11",
            "valueDate":"2020-11-11",
            "remittanceInformationUnstructured":"PAYMENT Alderaan Coffe"
         }
      ],
      "pending":[
         {
            "transactionAmount":{
               "currency":"EUR",
               "amount":"-10.00"
            },
            "valueDate":"2020-11-03",
            "remittanceInformationUnstructured":"Reserved PAYMENT Emperor's Burgers"
         }
      ]
   }
}   