# tuckdata

This repository contains a simple static frontend demonstrating a user journey
from sign up and login to a basic dashboard. All pages are located in the
`frontend/` directory and can be opened directly in a browser.

## Structure

- `frontend/index.html` – landing page with links to sign up or log in.
- `frontend/signup.html` – sign-up form storing user details in browser storage.
- `frontend/login.html` – login form that validates against saved credentials.
- `frontend/dashboard.html` – greeting page shown after successful login.
- `frontend/styles.css` – minimal styling inspired by OpenAI's clean interface.
- `frontend/script.js` – front-end logic using `localStorage`.

## Usage

Open `frontend/index.html` in a modern web browser to try out the flow. The demo
stores data in your browser's local storage and requires no backend.

### Running the Frontend

To serve the static files from a local server:

```bash
cd frontend
python -m http.server 8000
```

Then visit `http://localhost:8000/index.html` in your browser.

# TuckData Test Data Generator

This repository provides a minimal Flask application for generating test data via OpenAI. The app includes simple account management, wallet tracking, secret key creation and an API endpoint that proxies OpenAI requests. Stripe integration is stubbed for simplicity.

## Features

- **Register/Login/Logout**: Account management stored in MongoDB.
- **Secret Keys**: Users can create multiple API keys used for authentication.
- **JWT Sessions**: Login responses include a JWT that must be sent in the `Authorization` header.
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
   The application expects a running MongoDB instance. Configure the connection
   by setting the `MONGO_URI` environment variable. You can also override the
   JWT signing key with `JWT_SECRET`.

See `testdatagen/app.py` for endpoint details.
