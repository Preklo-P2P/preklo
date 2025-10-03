# Preklo - Pay anyone, instantly

Preklo is a mobile-first remittance and P2P payment application built on the Aptos blockchain, enabling instant, low-cost cross-border transfers using Circle USDC and native APT tokens.

## Project Overview

Preklo aims to be the "WhatsApp of money on Aptos" - a user-friendly payment app that makes crypto transfers as simple as sending a text message.

### Key Features

- **Circle USDC Integration**: Native USDC transfers on Aptos testnet
- **Username System**: Send money to `@username` instead of wallet addresses
- **Payment Links & QR Codes**: Generate shareable payment requests
- **Transaction Explorer**: Real-time transaction tracking with Nodit RPC integration
- **Mock Fiat On/Off Ramps**: Simulated USD deposit/withdrawal functionality
- **Comprehensive API**: RESTful API for all payment operations

## Documentation

For comprehensive documentation, see the [docs/](docs/) directory:

- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Complete technical overview and architecture
- **[Smart Contract Documentation](docs/SMART_CONTRACT_DOCUMENTATION.md)** - Move contracts reference and API
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete REST API reference with examples
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment and operations
- **[Business Plan](docs/BUSINESS_PLAN.md)** - Market analysis, strategy, and financial projections
- **[Case Studies](docs/CASE_STUDIES.md)** - Real-world application scenarios and impact analysis

## Architecture

### Smart Contracts (Move)
- **Username Registry**: Maps usernames to wallet addresses on-chain
- **Payment Forwarding**: Handles payment requests and escrow functionality

### Backend (Python FastAPI)
- **User Management**: User registration and profile management
- **Transaction Processing**: USDC/APT transfers with Aptos SDK
- **Payment Links**: QR code generation and payment request handling
- **Blockchain Integration**: Direct Aptos node and Nodit RPC connectivity
- **Database**: PostgreSQL with SQLAlchemy ORM

### Database Schema
- Users, Balances, Transactions, Payment Requests
- Fiat Transactions, Swap Transactions
- Full audit trail and transaction history

## Tech Stack

- **Blockchain**: Aptos Testnet
- **Smart Contracts**: Move language
- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Blockchain SDK**: Aptos Python SDK
- **RPC Provider**: Nodit (optional)
- **Authentication**: JWT tokens
- **QR Codes**: qrcode library with PIL

## Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Git
- Aptos CLI (for contract deployment)

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone git@github.com:daveylupes/Preklo.git
cd Preklo

# Run the setup script (handles everything automatically)
./setup.sh

# Follow the instructions to edit .env, then start the server
source venv/bin/activate
python -m backend.app.main
```

### Option 2: Manual Setup

```bash
# 1. Clone the repository
git clone git@github.com:daveylupes/Preklo.git
cd Preklo

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Database setup (requires PostgreSQL installed)
createdb aptossend

# 4. Environment configuration
cp env.example .env
nano .env  # Edit with your settings

# 5. Run database migrations
alembic upgrade head

# 6. Start the server
python -m backend.app.main
```

### Verify Installation

```bash
# Test the API
python test_api.py

# Or check health endpoint
curl http://localhost:8000/health
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Optional: Deploy Smart Contracts

```bash
cd move

# Initialize Aptos account (if needed)
aptos init

# Compile and deploy contracts
aptos move compile
aptos move publish
```

## API Documentation

### Core Endpoints

#### Health Check
```
GET /health - Check API and database status
```

#### User Management
```
POST /api/v1/users - Create new user
GET /api/v1/users/{user_id} - Get user by ID
GET /api/v1/users/username/{username} - Get user by username
PUT /api/v1/users/{user_id} - Update user
GET /api/v1/users/{user_id}/balances - Get user balances
POST /api/v1/users/{user_id}/sync-balances - Sync with blockchain
```

#### Username System
```
GET /api/v1/username/check/{username} - Check username availability
GET /api/v1/username/resolve/{username} - Resolve username to address
POST /api/v1/username/register - Register username on-chain
GET /api/v1/username/validate/{username} - Validate username format
GET /api/v1/username/search - Search usernames
```

#### Transactions
```
POST /api/v1/transactions/transfer - Create transfer
GET /api/v1/transactions - List transactions with filters
GET /api/v1/transactions/{transaction_id} - Get transaction by ID
GET /api/v1/transactions/hash/{tx_hash} - Get by blockchain hash
POST /api/v1/transactions/{transaction_id}/sync - Sync with blockchain
GET /api/v1/transactions/user/{user_id}/history - User transaction history
```

#### Payment Requests
```
POST /api/v1/payments/request - Create payment request
GET /api/v1/payments/request/{payment_id} - Get payment request
POST /api/v1/payments/pay - Pay payment request
GET /api/v1/payments/user/{user_id}/requests - User's payment requests
PUT /api/v1/payments/request/{payment_id}/cancel - Cancel payment request
GET /api/v1/payments/qr/{payment_id} - Get QR code
```

#### Fiat On/Off Ramps (Mock)
```
POST /api/v1/fiat/deposit - Mock fiat deposit
POST /api/v1/fiat/withdraw - Mock fiat withdrawal
GET /api/v1/fiat/transactions/{user_id} - Fiat transaction history
GET /api/v1/fiat/rates - Get exchange rates
GET /api/v1/fiat/limits - Get transaction limits
```

#### Blockchain Explorer
```
GET /api/v1/explorer/transaction/{tx_hash} - Get transaction details
GET /api/v1/explorer/account/{address}/transactions - Account transactions
GET /api/v1/explorer/account/{address}/balance-history - Balance history
POST /api/v1/explorer/sync/transaction/{tx_hash} - Sync transaction
GET /api/v1/explorer/stats/network - Network statistics
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest backend/tests/
```

### Code Quality

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Type checking
mypy backend/
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Security Considerations

- **Private Keys**: Never commit private keys to version control
- **API Keys**: Use environment variables for all sensitive data
- **JWT Secrets**: Generate strong, unique JWT secret keys
- **Database**: Use strong passwords and restrict access
- **CORS**: Configure CORS properly for production

## Deployment

### Production Environment

1. **Database**: Use managed PostgreSQL service
2. **API**: Deploy to cloud service (AWS, GCP, Azure)
3. **Environment**: Set production environment variables
4. **SSL/TLS**: Enable HTTPS for all endpoints
5. **Monitoring**: Set up logging and monitoring


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## API Examples

### Create User and Transfer USDC

```python
import requests

# Create user
user_data = {
    "username": "alice",
    "wallet_address": "0x123...",
    "email": "alice@example.com",
    "full_name": "Alice Johnson"
}
response = requests.post("http://localhost:8000/api/v1/users", json=user_data)
user = response.json()

# Transfer USDC
transfer_data = {
    "recipient": "@bob",  # Can use username or address
    "amount": "10.50",
    "currency_type": "USDC",
    "description": "Coffee payment"
}
response = requests.post(
    "http://localhost:8000/api/v1/transactions/transfer",
    json=transfer_data,
    params={"sender_private_key": "your_private_key"}
)
transaction = response.json()
```

### Create Payment Request

```python
# Create payment request
payment_data = {
    "amount": "25.00",
    "currency_type": "USDC",
    "description": "Dinner split",
    "expiry_hours": 24
}
response = requests.post(
    f"http://localhost:8000/api/v1/payments/request",
    json=payment_data,
    params={"recipient_id": user["id"]}
)
payment_request = response.json()

# Get QR code
qr_response = requests.get(
    f"http://localhost:8000/api/v1/payments/qr/{payment_request['data']['payment_id']}"
)
qr_data = qr_response.json()
print(f"Payment link: {qr_data['payment_link']}")
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Ensure database exists

2. **Aptos SDK Errors**
   - Verify APTOS_NODE_URL is correct
   - Check private key format
   - Ensure sufficient APT for gas fees

3. **Migration Errors**
   - Check database permissions
   - Verify alembic.ini configuration
   - Run migrations in order

### Logs and Debugging

```bash
# Enable debug logging
export DEBUG=True

# View application logs
tail -f logs/preklo.log

# Check database connections
psql -d aptossend -c "SELECT version();"
```

## Roadmap

### Phase 1 (Current) - MVP Backend + Contracts
- Smart contracts (username registry, payment forwarding)
- FastAPI backend with full CRUD operations
- USDC/APT transfer functionality
- Payment links and QR codes
- Transaction explorer with Nodit integration
- Mock fiat on/off ramps

### Phase 2 - Frontend & UX
- [ ] React/Next.js frontend application
- [ ] Mobile-responsive design
- [x] Wallet integration (Petra)
- [ ] Real-time notifications

### Phase 3 - Advanced Features
- [ ] Real fiat on/off ramp partnerships
- [ ] Token swap integration (Hyperion/Merkle Trade)
- [ ] Multi-signature wallets
- [ ] Merchant payment tools

### Phase 4 - Scale & Enterprise
- [ ] Cross-chain integration (Panora)
- [ ] Enterprise payroll tools
- [ ] Advanced analytics dashboard
- [ ] Mobile apps (iOS/Android)

## Support

- **Documentation**: Check this README and API docs
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub Discussions for questions
- **Email**: support@aptossend.com (if available)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Aptos Labs** for the blockchain platform
- **Circle** for USDC integration
- **Nodit** for RPC infrastructure
- **FastAPI** for the excellent web framework
- **SQLAlchemy** for database ORM

---

**Preklo** - Pay anyone, instantly.