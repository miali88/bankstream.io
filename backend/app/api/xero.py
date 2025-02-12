from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

XERO_API_URL = "https://api.xero.com/api.xro/2.0/Accounts"
ACCESS_TOKEN = "your_access_token_here"

# class ChartOfAccountsResponse(BaseModel):


@app.get("/chart-of-accounts")
async def get_chart_of_accounts():
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(XERO_API_URL, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch accounts")
        
        return response.json()


