# Agentic AI Trading Application

A full-stack algorithmic trading platform built with FastAPI (Backend) and React (Frontend).

## Prerequisites

- Python 3.11+
- Node.js (for frontend)
- Kotak Neo API Credentials

## Setup

### Backend

1.  **Environment Setup**
    The project uses a virtual environment `.venv`.
    
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r backend/requirements.txt
    ```

2.  **Configuration**
    Edit `backend/.env` with your credentials:
    ```env
    KOTAK_ACCESS_TOKEN=your_token
    MOBILE_NUMBER=your_mobile
    UCC=your_client_code
    MPIN=your_mpin
    ```

3.  **Run Application**
    ```bash
    cd backend
    ../.venv/bin/uvicorn app.main:app --reload
    ```
    API Docs: http://localhost:8000/docs

### Frontend

1.  **Install Dependencies**
    ```bash
    cd frontend
    npm install
    ```

2.  **Run Development Server**
    ```bash
    npm run dev
    ```
    
## Features

- **Auth**: Logic for TOTP/MPIN flow.
- **Market Data**: Quotes and WebSocket connectivity.
- **Orders**: Place, Modify, Cancel orders.
- **Portfolio**: View holdings and limits.
- **Strategy**: Background engine for automated strategies.

## Project Structure

- `backend/app`: Core logic (clean architecture).
- `frontend/src`: UI components (React).
