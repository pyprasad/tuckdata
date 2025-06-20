# TuckData Test Data Generator

This repository provides a minimal Flask application for generating test data via OpenAI. The app includes simple account management, wallet tracking, secret key creation and an API endpoint that proxies OpenAI requests. Stripe integration is stubbed for simplicity.

## Features

- **Register/Login/Logout**: Basic account management backed by SQLite.
- **Secret Keys**: Users can create multiple API keys used for authentication.
- **Wallet**: Deposits update a user's wallet balance. Charges are applied when generating data.
- **OpenAI Proxy**: Requests to OpenAI are forwarded and usage is recorded. Costs are multiplied by a configurable factor.
- **Usage Tracking**: Each request stores token usage and cost so users can review their spending.
- **Stripe Skeleton**: The `/deposit` endpoint demonstrates where Stripe payment handling would occur.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python testdatagen/app.py
```

3. The API will be available at `http://localhost:5000`.

See `testdatagen/app.py` for endpoint details.
