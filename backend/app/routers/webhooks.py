"""
Webhook Handlers
Processes incoming webhooks from Unlimit and other services
"""

import json
from fastapi import APIRouter, Request, HTTPException, status, Depends, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import UnlimitWebhook, UnlimitCard, UnlimitTransaction
from ..schemas import UnlimitWebhookPayload, CardAuthorizationRequest, ApiResponse
from ..services.unlimit_service import unlimit_service

router = APIRouter()


@router.post("/unlimit", response_model=ApiResponse)
async def handle_unlimit_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_webhook_id: Optional[str] = Header(None, alias="X-Webhook-ID")
):
    """
    Handle incoming webhooks from Unlimit
    Based on Unlimit webhook documentation
    """
    try:
        # Get raw payload
        payload = await request.body()
        payload_str = payload.decode('utf-8')
        
        # Verify webhook signature
        if not unlimit_service.verify_webhook(payload_str, x_signature or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook data
        webhook_data = json.loads(payload_str)
        
        # Store webhook for processing
        db_webhook = UnlimitWebhook(
            webhook_id=x_webhook_id or webhook_data.get("webhook_id", "unknown"),
            event_type=webhook_data.get("event_type", "unknown"),
            status="received",
            payload=payload_str,
            signature=x_signature
        )
        
        db.add(db_webhook)
        db.commit()
        db.refresh(db_webhook)
        
        # Process webhook in background
        background_tasks.add_task(
            process_unlimit_webhook,
            db_webhook.id,
            webhook_data
        )
        
        return ApiResponse(
            success=True,
            message="Webhook received and queued for processing",
            data={"webhook_id": db_webhook.webhook_id}
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        print(f"Error handling Unlimit webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


async def process_unlimit_webhook(webhook_id: str, webhook_data: dict):
    """
    Background task to process Unlimit webhook events
    """
    from ..database import SessionLocal, get_session_local
    
    session_local = SessionLocal if SessionLocal is not None else get_session_local()
    db = session_local()
    try:
        # Get webhook record
        webhook = db.query(UnlimitWebhook).filter(
            UnlimitWebhook.id == webhook_id
        ).first()
        
        if not webhook:
            print(f"Webhook {webhook_id} not found")
            return
        
        event_type = webhook_data.get("event_type")
        event_data = webhook_data.get("data", {})
        
        print(f"Processing webhook: {event_type}")
        
        if event_type == "card.transaction.authorization_requested":
            await handle_authorization_request(event_data, db)
        
        elif event_type == "card.transaction.authorized":
            await handle_transaction_authorized(event_data, db)
        
        elif event_type == "card.transaction.settled":
            await handle_transaction_settled(event_data, db)
        
        elif event_type == "card.transaction.declined":
            await handle_transaction_declined(event_data, db)
        
        elif event_type == "card.created":
            await handle_card_created(event_data, db)
        
        elif event_type == "card.status_changed":
            await handle_card_status_changed(event_data, db)
        
        else:
            print(f"Unhandled webhook event type: {event_type}")
        
        # Mark webhook as processed
        webhook.status = "processed"
        webhook.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        print(f"Error processing webhook {webhook_id}: {e}")
        
        # Mark webhook as failed
        webhook = db.query(UnlimitWebhook).filter(
            UnlimitWebhook.id == webhook_id
        ).first()
        
        if webhook:
            webhook.status = "failed"
            webhook.error_message = str(e)
            webhook.retry_count += 1
            db.commit()
    
    finally:
        db.close()


async def handle_authorization_request(event_data: dict, db: Session):
    """
    Handle real-time authorization request
    This is the critical path for card transactions
    """
    try:
        # Extract authorization data
        transaction_id = event_data.get("transaction_id")
        card_id = event_data.get("card_id")
        amount = float(event_data.get("amount", 0))
        currency = event_data.get("currency", "USD")
        merchant_name = event_data.get("merchant", {}).get("name")
        merchant_category = event_data.get("merchant", {}).get("category_code")
        
        # Create authorization request
        auth_request = CardAuthorizationRequest(
            transaction_id=transaction_id,
            card_id=card_id,
            amount=amount,
            currency=currency,
            merchant_name=merchant_name,
            merchant_category=merchant_category
        )
        
        # Process authorization through service
        auth_response = await unlimit_service.authorize_transaction(auth_request, db)
        
        # Send response back to Unlimit (in real implementation)
        # This would be an API call back to Unlimit with the authorization decision
        print(f"Authorization response for {transaction_id}: {auth_response.approved}")
        
        # In real implementation, you'd make an API call like:
        # await unlimit_service.send_authorization_response(transaction_id, auth_response)
        
    except Exception as e:
        print(f"Error handling authorization request: {e}")
        raise


async def handle_transaction_authorized(event_data: dict, db: Session):
    """
    Handle transaction authorization confirmation
    """
    try:
        transaction_id = event_data.get("transaction_id")
        
        # Update transaction status
        transaction = db.query(UnlimitTransaction).filter(
            UnlimitTransaction.unlimit_transaction_id == transaction_id
        ).first()
        
        if transaction:
            transaction.transaction_status = "authorized"
            transaction.auth_code = event_data.get("auth_code")
            db.commit()
            print(f"Transaction {transaction_id} marked as authorized")
        
    except Exception as e:
        print(f"Error handling transaction authorized: {e}")


async def handle_transaction_settled(event_data: dict, db: Session):
    """
    Handle transaction settlement
    """
    try:
        transaction_id = event_data.get("transaction_id")
        settlement_amount = float(event_data.get("settlement_amount", 0))
        
        # Process settlement through service
        success = await unlimit_service.process_settlement(
            transaction_id, settlement_amount, db
        )
        
        if success:
            print(f"Transaction {transaction_id} settled for {settlement_amount}")
        else:
            print(f"Failed to process settlement for {transaction_id}")
        
    except Exception as e:
        print(f"Error handling transaction settlement: {e}")


async def handle_transaction_declined(event_data: dict, db: Session):
    """
    Handle declined transaction
    """
    try:
        transaction_id = event_data.get("transaction_id")
        decline_reason = event_data.get("decline_reason")
        
        # Update transaction status
        transaction = db.query(UnlimitTransaction).filter(
            UnlimitTransaction.unlimit_transaction_id == transaction_id
        ).first()
        
        if transaction:
            transaction.transaction_status = "declined"
            transaction.decline_reason = decline_reason
            
            # Refund the reserved balance
            from ..models import Balance
            user_balance = db.query(Balance).filter(
                Balance.user_id == transaction.user_id,
                Balance.currency_type == "USDC"
            ).first()
            
            if user_balance:
                user_balance.balance += transaction.amount  # Refund
                transaction.wallet_balance_after = user_balance.balance
            
            db.commit()
            print(f"Transaction {transaction_id} declined: {decline_reason}")
        
    except Exception as e:
        print(f"Error handling transaction declined: {e}")


async def handle_card_created(event_data: dict, db: Session):
    """
    Handle card creation confirmation
    """
    try:
        card_id = event_data.get("card_id")
        
        # Update card status in database
        card = db.query(UnlimitCard).filter(
            UnlimitCard.unlimit_card_id == card_id
        ).first()
        
        if card:
            card.card_status = event_data.get("status", "active")
            card.last_four = event_data.get("last_four")
            card.expiry_month = event_data.get("expiry_month")
            card.expiry_year = event_data.get("expiry_year")
            db.commit()
            print(f"Card {card_id} creation confirmed")
        
    except Exception as e:
        print(f"Error handling card created: {e}")


async def handle_card_status_changed(event_data: dict, db: Session):
    """
    Handle card status changes
    """
    try:
        card_id = event_data.get("card_id")
        new_status = event_data.get("new_status")
        
        # Update card status in database
        card = db.query(UnlimitCard).filter(
            UnlimitCard.unlimit_card_id == card_id
        ).first()
        
        if card:
            card.card_status = new_status
            db.commit()
            print(f"Card {card_id} status changed to {new_status}")
        
    except Exception as e:
        print(f"Error handling card status change: {e}")


@router.get("/unlimit/test", response_model=ApiResponse)
async def test_unlimit_webhook(db: Session = Depends(get_db)):
    """
    Test endpoint for webhook processing
    """
    # Create test webhook data
    test_webhook_data = {
        "event_type": "card.transaction.authorization_requested",
        "webhook_id": "test_webhook_123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "transaction_id": "test_txn_123",
            "card_id": "test_card_123",
            "amount": 25.00,
            "currency": "USD",
            "merchant": {
                "name": "Test Merchant",
                "category_code": "5411"
            }
        }
    }
    
    # Store test webhook
    db_webhook = UnlimitWebhook(
        webhook_id="test_webhook_123",
        event_type="card.transaction.authorization_requested",
        status="received",
        payload=json.dumps(test_webhook_data),
        signature="test_signature"
    )
    
    db.add(db_webhook)
    db.commit()
    
    # Process webhook
    await process_unlimit_webhook(str(db_webhook.id), test_webhook_data)
    
    return ApiResponse(
        success=True,
        message="Test webhook processed",
        data={"webhook_id": "test_webhook_123"}
    )
