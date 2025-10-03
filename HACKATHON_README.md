# Preklo - CTRL+MOVE Hackathon Submission

**The WhatsApp of Money - Instant Cross-Border Payments on Aptos**

## Project Overview

Preklo is a revolutionary mobile-first remittance platform that transforms cross-border payments by leveraging Aptos blockchain and Circle USDC. We eliminate the high fees and slow processing times that plague traditional remittance services, while providing a user experience as simple as sending a text message.

**Send money anywhere using simple names like johnsmith - fast, secure, and affordable.**

## Hackathon Alignment

### Primary Track: Payments & Money Movement
- **Global remittance and P2P payment apps using stablecoins** ✓
- **Fiat on/off-ramps for real-world utility** ✓
- **Cross-border payments** ✓

### Secondary Track: Trading & Market Infrastructure
- **Composability with Aptos-native platforms** ✓
- **Mobile-first UIs** ✓

## Key Innovations

### 1. Username System
- Send money to `@username` instead of complex wallet addresses
- On-chain username registry using Move smart contracts
- Human-readable payment addresses

### 2. Circle USDC Integration
- Real stablecoin implementation with Circle API
- Programmable wallet support
- Compliance-ready infrastructure

### 3. Payment Links & QR Codes
- Generate shareable payment requests
- QR code generation for easy sharing
- Expiry-based payment requests

### 4. Fee Collection System
- Sustainable revenue model with transaction fees
- Multi-tier fee structure (P2P, cross-border, merchant)
- On-chain fee collection and withdrawal

## Technical Implementation

### Smart Contracts (Move)
- **Username Registry**: Maps usernames to wallet addresses
- **Payment Forwarding**: Handles payment requests and escrow
- **Fee Collector**: Manages transaction fees and revenue

### Backend (Python FastAPI)
- **User Management**: Registration and profile management
- **Transaction Processing**: USDC/APT transfers with Aptos SDK
- **Circle Integration**: Real USDC operations
- **Database**: PostgreSQL with full audit trail

### Frontend (React/TypeScript)
- **Mobile-First Design**: Responsive UI for global accessibility
- **Petra Wallet Integration**: Seamless wallet connection
- **Real-Time Updates**: Live transaction tracking
- **Payment Flows**: Intuitive send/receive interfaces

## Impact & Market

### Target Market
- **281 million migrant workers** globally
- **$800 billion** in annual remittances
- **6-8% average fees** in traditional systems

### Our Solution
- **Under 1% fees** with Preklo
- **Instant settlement** on Aptos blockchain
- **Global accessibility** with mobile-first design

## Demo Features

### User Registration
1. Create account with username
2. Automatic wallet creation (custodial option)
3. Connect external wallet (Petra)

### Sending Money
1. Enter recipient username (`@bob`)
2. Specify amount in USDC
3. Add message/description
4. Confirm and send instantly

### Payment Requests
1. Generate payment link
2. Share via QR code or URL
3. Recipient pays with one click
4. Automatic settlement

### Fee Collection
1. Platform collects small fees
2. Multi-tier pricing structure
3. Sustainable revenue model

## Technical Excellence

### Advanced Move Contracts
- Multiple interacting modules
- Gas-optimized operations
- Event-driven architecture
- Error handling and validation

### Full-Stack Architecture
- Production-ready backend API
- Comprehensive database schema
- Real-time frontend updates
- Circle USDC integration

### Security & Compliance
- JWT authentication
- Input validation and sanitization
- Rate limiting and CORS
- Audit trail and logging

## Repository Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models.py       # Database models
│   │   └── main.py         # Application entry
│   └── migrations/         # Database migrations
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Application pages
│   │   ├── lib/            # Utilities and API client
│   │   └── store/          # State management
├── move/                   # Smart contracts
│   ├── sources/
│   │   ├── username_registry.move
│   │   └── payment_forwarding.move
└── docs/                   # Documentation
    ├── TECHNICAL_DOCUMENTATION.md
    ├── API_DOCUMENTATION.md
    └── DEPLOYMENT_GUIDE.md
```

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 13+
- Node.js 18+
- Aptos CLI

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Smart Contracts
```bash
cd move
aptos move compile
aptos move publish
```

## Live Demo

- **Frontend**: [Deploy to Vercel/Netlify]
- **Backend**: [Deploy to Railway/Heroku]
- **Smart Contracts**: Deployed on Aptos Testnet
- **Contract Address**: `0xa3bbeb9cc35bab4c3c0af22c9b1398e4d849d4b33ed59b59a6dc4b1ca5298a2d`

## Why Preklo Wins

### 1. Real-World Impact
- Solves actual problem (high remittance fees)
- Targets massive market (281M users, $800B volume)
- Immediate utility and adoption potential

### 2. Technical Innovation
- Advanced Move smart contracts
- Circle USDC integration
- Full-stack production architecture
- Mobile-first design

### 3. Business Viability
- Sustainable revenue model
- Scalable infrastructure
- Compliance-ready
- Market-proven demand

### 4. User Experience
- Simple as sending a text message
- No technical knowledge required
- Global accessibility
- Instant settlement

## Contact

- **GitHub**: [Repository URL]
- **Demo Video**: [YouTube/Vimeo Link]
- **Live Demo**: [Deployed URL]
- **Documentation**: [Full docs in /docs directory]

---

**Preklo - Pay anyone, instantly. Built for the future of global payments on Aptos.**
