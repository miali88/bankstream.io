# BankStream API

A FastAPI-based banking API with Clerk authentication, GoCardless payments, and Supabase database integration.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```env
CLERK_API_KEY=your_clerk_api_key
CLERK_JWT_KEY=your_clerk_jwt_key
GOCARDLESS_ACCESS_TOKEN=your_gocardless_token
GOCARDLESS_ENVIRONMENT=sandbox  # or 'live' for production
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. Run the server:
```bash
uvicorn main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Routes

### Authentication (Clerk)
- POST `/auth/login` - Login with Clerk token
- GET `/auth/me` - Get current user
- POST `/auth/logout` - Logout user

### Payments (GoCardless)
- POST `/payments/create-payment` - Create a new payment
- GET `/payments/payments` - List all payments
- POST `/payments/setup-mandate` - Setup a new mandate
- GET `/payments/mandates` - List all mandates

### Database (Supabase)
- POST `/db/transactions` - Create a new transaction
- GET `/db/transactions` - List all transactions
- GET `/db/transactions/{transaction_id}` - Get a specific transaction
- PUT `/db/transactions/{transaction_id}` - Update a transaction
- DELETE `/db/transactions/{transaction_id}` - Delete a transaction
