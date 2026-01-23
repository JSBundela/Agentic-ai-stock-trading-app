# Kotak Neo Trading App - Frontend

React + TypeScript + Tailwind CSS frontend for Kotak Neo Trading Platform.

## Phase 1 - Core Trading UI

**Status:** ✅ Complete

### Features
- ✅ Two-factor authentication (TOTP + MPIN)
- ✅ Dashboard with margin and order statistics
- ✅ Order placement (Buy/Sell, Regular/AMO, Limit/Market)
- ✅ Live order book with auto-refresh
- ✅ Order modification and cancellation

## Prerequisites

- Node.js 18+ (`node --version`)
- Backend running on `http://localhost:8000`

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Copy environment file (if not exists)
cp .env.example .env

# 3. Start development server
npm run dev

# 4. Open browser
# Frontend: http://localhost:5173
# Backend must be running on http://localhost:8000
```

## Backend APIs Used

**Authentication:**
- `POST /auth/totp-login` - TOTP authentication
- `POST /auth/validate-mpin` - MPIN validation

**Orders:**
- `POST /orders/place` - Place order
- `GET /orders/order-book` - Fetch all orders
- `POST /orders/modify` - Modify order
- `DELETE /orders/{id}` - Cancel order

**Portfolio:**
- `GET /portfolio/limits` - Get margin/limits

## Environment Variables

```
VITE_API_URL=http://localhost:8000
```

## Development

```bash
npm run dev  # Start dev server
npm run build  # Production build
```

---

**Frontend:** Production Ready ✅  
**Backend:** Frozen & Verified ✅  
**Integration:** Complete ✅
