from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from .config import settings
from .database import get_db
from .routers import users, transactions, payments, fiat, username, health, explorer, auth, circle, cards, webhooks, fees, notifications, blockchain, send_money, wallet, receive_money, transaction_history, transaction_limits, payment_requests, vouchers, security
from .dependencies import RateLimitMiddleware
from .utils.error_handlers import setup_error_handlers
from .utils.logging import setup_logging
from .utils.validation import validate_startup_environment
from .middleware.security import SecurityHeadersMiddleware, RequestTrackingMiddleware, UserContextMiddleware

# Setup logging
setup_logging(debug=settings.debug)

# Validate environment (warn only in development)
if not validate_startup_environment():
    if not settings.debug:
        import sys
        print("CRITICAL: Environment validation failed. Please check your configuration.")
        sys.exit(1)
    else:
        print("WARNING: Environment validation failed - continuing in debug mode")

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="Preklo - Pay anyone, instantly",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware (order matters - add from outer to inner)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(UserContextMiddleware)

# Add rate limiting middleware
app.middleware("http")(RateLimitMiddleware(requests_per_minute=120))

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix=settings.api_v1_str + "/auth", tags=["Authentication"])
app.include_router(users.router, prefix=settings.api_v1_str + "/users", tags=["Users"])
app.include_router(username.router, prefix=settings.api_v1_str + "/username", tags=["Username"])
# Include transaction_history BEFORE transactions to ensure /history route matches before /{transaction_id}
app.include_router(transaction_history.router, prefix=settings.api_v1_str + "/transactions", tags=["Transaction History"])
app.include_router(transactions.router, prefix=settings.api_v1_str + "/transactions", tags=["Transactions"])
app.include_router(payments.router, prefix=settings.api_v1_str + "/payments", tags=["Payments"])
app.include_router(fiat.router, prefix=settings.api_v1_str + "/fiat", tags=["Fiat"])
app.include_router(circle.router, prefix=settings.api_v1_str + "/circle", tags=["Circle USDC"])
app.include_router(cards.router, prefix=settings.api_v1_str + "/cards", tags=["Cards"])
app.include_router(webhooks.router, prefix=settings.api_v1_str + "/webhooks", tags=["Webhooks"])
app.include_router(fees.router, prefix=settings.api_v1_str + "/fees", tags=["Fees"])
app.include_router(explorer.router, prefix=settings.api_v1_str + "/explorer", tags=["Explorer"])
app.include_router(notifications.router, prefix=settings.api_v1_str + "/notifications", tags=["Notifications"])
app.include_router(blockchain.router, prefix=settings.api_v1_str + "/blockchain", tags=["Blockchain"])
app.include_router(send_money.router, prefix=settings.api_v1_str + "/send-money", tags=["Send Money"])
app.include_router(receive_money.router, prefix=settings.api_v1_str + "/receive-money", tags=["Receive Money"])
app.include_router(transaction_limits.router, prefix=settings.api_v1_str + "/limits", tags=["Transaction Limits"])
app.include_router(payment_requests.router, prefix=settings.api_v1_str, tags=["Payment Requests"])
app.include_router(vouchers.router, prefix=settings.api_v1_str + "/vouchers", tags=["Vouchers"])
app.include_router(security.router, prefix=settings.api_v1_str + "/security", tags=["Security"])
app.include_router(wallet.router, prefix=settings.api_v1_str + "/wallet", tags=["Wallet"])

# Setup error handlers
setup_error_handlers(app)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Preklo API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
