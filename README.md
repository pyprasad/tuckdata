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
