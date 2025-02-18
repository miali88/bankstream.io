# 🏦 Bankstream AI

Bankstream AI is your intelligent financial data aggregation platform that keeps your accounts synchronized and enriched in real-time.

## 🌟 Features

- 🔄 Real-time bank data synchronization
- 📊 Automated transaction categorization
- 🤖 AI-powered transaction enrichment
- 📚 Smart accounting software integration
- 🔍 Intelligent reconciliation
- 🔐 Secure multi-bank connectivity

## 🛠️ Tech Stack

### Frontend
- 🎨 Remix.js - React-based web framework
- 🎭 Clerk - Authentication and user management
- 💅 Tailwind CSS - Utility-first CSS framework
- 🔷 TypeScript - Type-safe JavaScript
- 📊 TanStack Table - Powerful table components

### Backend
- ⚡ FastAPI - Modern Python web framework
- 🔒 Supabase - PostgreSQL database
- 🏦 GoCardless - Bank connectivity
- 📚 Xero - Accounting integration
- 🔗 Plaid - Financial data enrichment
- 🤖 OpenAI - LLM for transaction analysis

## 🚀 Getting Started

### Frontend Setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Start the development server:
    ```bash
    npm run dev
    ```

### Backend Setup
1. Install dependencies:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```

2. Create `.env` file:
    ```bash
    cp .env.example .env
    ```

3. Start the server:
    ```bash
    python run_fast.py
    ```


## 🗺️ Roadmap

- [ ] Automated 1 click reconciliation
- [ ] Dashboard with financial insights
- [ ] Self improving reconciliation that learns from user feedback
- [ ] Email inbox monitoring to store accounting related data and match with transactions


## 📚 Documentation

- [API Documentation](http://localhost:8000/docs)

## 🤝 Contributing

We welcome contributions!

## 📄 License

This project is licensed under the GNU AFFERO GENERAL PUBLIC LICENSE - see the [LICENSE](LICENSE) file for details.

## 💬 Support

For support, email support@bankstream.ai or join our [Discord community](https://discord.gg/bankstream).