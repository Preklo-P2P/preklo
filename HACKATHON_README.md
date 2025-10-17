# Preklo - CTRL+MOVE Hackathon Submission

**The WhatsApp of Money - Instant Cross-Border Payments on Aptos**

## Project Overview

Preklo is a revolutionary mobile-first remittance platform that transforms cross-border payments by leveraging Aptos blockchain and Circle USDC. We eliminate the high fees and slow processing times that plague traditional remittance services, while providing a user experience as simple as sending a text message.

**Send money anywhere using simple names like johnsmith - fast, secure, and affordable.**

## The Problem

The global remittance industry is broken. Every year, 281 million migrant workers send over $800 billion to their families back home, but they're forced to pay exorbitant fees averaging 6-8% per transaction through traditional services like Western Union, MoneyGram, and traditional banks. These fees can consume up to 20% of a worker's monthly income, creating a massive financial burden on families who can least afford it. Beyond the high costs, traditional remittance services are plagued by slow processing times (often taking 3-5 business days), complex verification processes, limited accessibility in rural areas, and lack of transparency in fee structures. Additionally, 1.7 billion adults worldwide remain unbanked, completely excluded from the traditional financial system. The current system perpetuates financial inequality and creates barriers to economic mobility for the world's most vulnerable populations. These challenges are compounded by the COVID-19 pandemic, which has made in-person remittance services even more difficult to access, highlighting the urgent need for digital-first solutions that can operate across borders without physical infrastructure.

## The Solution

Preklo revolutionizes global payments by combining the power of blockchain technology with the simplicity of modern messaging apps. Our platform enables users to send money anywhere in the world using simple usernames like "@johnsmith" instead of complex wallet addresses, making cryptocurrency as easy to use as sending a text message. Built on the Aptos blockchain with Circle USDC integration, Preklo delivers instant settlements with fees under 1% - a 85% reduction compared to traditional services. The platform features a comprehensive username registry system powered by Move smart contracts, allowing users to create memorable payment addresses that never change, even if they switch wallets. Our mobile-first design ensures global accessibility, working seamlessly on any smartphone without requiring users to understand blockchain technology. The platform supports both custodial wallets for beginners and integration with external wallets like Petra for advanced users, providing flexibility while maintaining security. Payment requests can be generated as shareable links or QR codes, enabling easy money collection for businesses and individuals. The system includes real-time notifications, transaction history, and comprehensive security features including JWT authentication, input validation, and audit trails. By making the benefits of blockchain technology invisible to end users, Preklo bridges the gap between traditional finance and the future of money, creating a truly inclusive financial system.

## Future Features

Preklo's roadmap extends far beyond basic remittance services, envisioning a comprehensive financial ecosystem that transforms how people interact with money globally. Our next phase includes advanced merchant payment solutions, enabling businesses to accept payments through usernames with integrated point-of-sale systems and automated invoicing. We're developing a sophisticated multi-currency support system that will allow users to hold and exchange multiple stablecoins and cryptocurrencies, with intelligent routing to minimize fees and maximize conversion rates. The platform will introduce savings and investment features, including automated dollar-cost averaging into cryptocurrency portfolios and yield-generating products that help users grow their wealth over time. We're building a comprehensive marketplace integration system that will allow users to make purchases directly from merchants using their Preklo balance, creating a seamless e-commerce experience. Advanced features include programmable money capabilities, allowing users to set up automatic recurring payments, conditional transfers, and smart contracts for complex financial arrangements. The platform will incorporate advanced analytics and financial insights, providing users with spending patterns, budget recommendations, and personalized financial advice. We're developing a robust API ecosystem that will enable third-party developers to build applications on top of Preklo, creating a thriving ecosystem of financial services. Future integrations include partnerships with local banks for fiat on/off-ramps, integration with major e-commerce platforms, and support for emerging payment methods like central bank digital currencies (CBDCs). The platform will also introduce social features, allowing users to split bills, create group payments, and share financial goals with family members. Advanced security features will include biometric authentication, hardware wallet integration, and sophisticated fraud detection systems powered by machine learning. Our long-term vision includes expanding into emerging markets with localized features, regulatory compliance frameworks for different jurisdictions, and partnerships with local financial institutions to ensure widespread adoption and regulatory acceptance.

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

## Team

### Core Team
**Davey** - Full-Stack Developer & Project Lead

Davey is a seasoned full-stack developer with extensive expertise in blockchain development, fintech solutions, and modern web technologies. With a strong background in both frontend and backend development, Davey has successfully architected and implemented the complete Preklo platform from the ground up. His technical contributions span the entire technology stack, including designing and implementing the complete backend API with FastAPI and PostgreSQL, developing sophisticated Move smart contracts for username registry and payment forwarding on the Aptos blockchain, building a responsive React frontend with TypeScript and mobile-first design principles, integrating Circle USDC API for real stablecoin operations, and implementing comprehensive security and authentication systems. Davey's approach combines deep technical knowledge with a user-centric mindset, ensuring that complex blockchain technology remains invisible to end users while delivering the benefits of instant, low-cost global payments. His full-stack expertise enables seamless integration between smart contracts, backend services, and frontend interfaces, creating a cohesive and production-ready platform that addresses real-world market needs.

### Technical Expertise
- **Blockchain Development**: Move smart contracts, Aptos SDK, wallet integration
- **Backend Development**: Python FastAPI, PostgreSQL, RESTful APIs
- **Frontend Development**: React, TypeScript, mobile-responsive design
- **Fintech Integration**: Circle USDC API, payment processing, compliance
- **DevOps**: Database migrations, deployment automation, testing

### Development Approach
- **User-Centric Design**: Focused on making crypto benefits invisible to end users
- **Production-Ready**: Built with scalability, security, and compliance in mind
- **Mobile-First**: Designed for global accessibility across all devices
- **Real-World Impact**: Targeting actual market needs with sustainable business model

### Hackathon Journey
- **Problem Identification**: Recognized the $4.39T global remittance market opportunity
- **Solution Design**: Created username-based payment system for mass adoption
- **Technical Implementation**: Full-stack development with real blockchain integration
- **User Experience**: Simplified complex crypto operations into familiar interactions
- **Market Validation**: Built for 1.7B unbanked adults and 281M migrant workers

## Contact

- **GitHub**: https://github.com/Preklo-P2P/preklo
- **Demo Video**: [YouTube/Vimeo Link]
- **Live Demo**: [Deployed URL]

---

**Preklo - Pay anyone, instantly. Built for the future of global payments on Aptos.**
