"""
Transaction History Service for Story 2.5
Enhanced transaction history with filtering, search, export, and analytics
"""

import logging
import csv
import io
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from ..models import User, Transaction, Balance
from ..schemas import ApiResponse

logger = logging.getLogger("preklo.transaction_history_service")


class TransactionHistoryService:
    """Enhanced transaction history service with advanced features"""
    
    def __init__(self):
        self._export_cache: Dict[str, Dict[str, Any]] = {}
        self._analytics_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_enhanced_transaction_history(
        self,
        user: User,
        db: Session,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get enhanced transaction history with advanced filtering and search
        """
        try:
            # Build base query
            query = self._build_base_query(user, db)
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Apply search
            if search_query:
                query = self._apply_search(query, search_query)
            
            # Apply sorting
            query = self._apply_sorting(query, sort_by, sort_order)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            results = query.offset(offset).limit(limit).all()
            
            # Transform results
            transactions = self._transform_transaction_results(results)
            
            # Calculate pagination info
            pagination = {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            }
            
            return {
                "transactions": transactions,
                "pagination": pagination,
                "filters_applied": filters or {},
                "search_query": search_query
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced transaction history: {e}")
            return {
                "transactions": [],
                "pagination": {"total": 0, "limit": limit, "offset": offset, "has_next": False, "has_prev": False},
                "filters_applied": {},
                "search_query": search_query
            }
    
    def _build_base_query(self, user: User, db: Session):
        """Build base query for user transactions"""
        from sqlalchemy.orm import aliased
        SenderUser = aliased(User)
        RecipientUser = aliased(User)
        
        return db.query(Transaction, SenderUser, RecipientUser).outerjoin(
            SenderUser, Transaction.sender_id == SenderUser.id
        ).outerjoin(
            RecipientUser, Transaction.recipient_id == RecipientUser.id
        ).filter(
            or_(Transaction.sender_id == user.id, Transaction.recipient_id == user.id)
        )
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply advanced filters to query"""
        # Date range filter
        if "start_date" in filters and filters["start_date"]:
            start_date = datetime.fromisoformat(filters["start_date"].replace("Z", "+00:00"))
            query = query.filter(Transaction.created_at >= start_date)
        
        if "end_date" in filters and filters["end_date"]:
            end_date = datetime.fromisoformat(filters["end_date"].replace("Z", "+00:00"))
            query = query.filter(Transaction.created_at <= end_date)
        
        # Amount range filter
        if "min_amount" in filters and filters["min_amount"]:
            query = query.filter(Transaction.amount >= Decimal(str(filters["min_amount"])))
        
        if "max_amount" in filters and filters["max_amount"]:
            query = query.filter(Transaction.amount <= Decimal(str(filters["max_amount"])))
        
        # Status filter
        if "status" in filters and filters["status"]:
            query = query.filter(Transaction.status == filters["status"])
        
        # Currency type filter
        if "currency_type" in filters and filters["currency_type"]:
            query = query.filter(Transaction.currency_type == filters["currency_type"])
        
        # Transaction type filter
        if "transaction_type" in filters and filters["transaction_type"]:
            query = query.filter(Transaction.transaction_type == filters["transaction_type"])
        
        # Direction filter (sent/received)
        if "direction" in filters and filters["direction"]:
            if filters["direction"] == "sent":
                query = query.filter(Transaction.sender_id == query.column_descriptions[0]["entity"].id)
            elif filters["direction"] == "received":
                query = query.filter(Transaction.recipient_id == query.column_descriptions[0]["entity"].id)
        
        return query
    
    def _apply_search(self, query, search_query: str):
        """Apply text search to query"""
        search_term = f"%{search_query}%"
        
        # Search in transaction hash
        query = query.filter(
            or_(
                Transaction.transaction_hash.ilike(search_term),
                Transaction.description.ilike(search_term)
            )
        )
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to query"""
        if sort_by == "amount":
            if sort_order == "desc":
                query = query.order_by(desc(Transaction.amount))
            else:
                query = query.order_by(asc(Transaction.amount))
        elif sort_by == "status":
            if sort_order == "desc":
                query = query.order_by(desc(Transaction.status))
            else:
                query = query.order_by(asc(Transaction.status))
        else:  # Default to created_at
            if sort_order == "desc":
                query = query.order_by(desc(Transaction.created_at))
            else:
                query = query.order_by(asc(Transaction.created_at))
        
        return query
    
    def _transform_transaction_results(self, results: List[Tuple]) -> List[Dict[str, Any]]:
        """Transform query results to response format"""
        transactions = []
        
        for result in results:
            transaction = result[0]  # Transaction object
            sender_user = result[1]  # Sender User object
            recipient_user = result[2]  # Recipient User object
            
            transaction_dict = {
                "id": str(transaction.id),
                "transaction_hash": transaction.transaction_hash,
                "amount": str(transaction.amount),
                "currency_type": transaction.currency_type,
                "transaction_type": transaction.transaction_type,
                "status": transaction.status,
                "description": transaction.description,
                "gas_fee": str(transaction.gas_fee) if transaction.gas_fee else None,
                "block_height": transaction.block_height,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None,
                "sender": {
                    "id": str(sender_user.id) if sender_user else None,
                    "username": sender_user.username if sender_user else None,
                    "wallet_address": sender_user.wallet_address if sender_user else None,
                    "full_name": sender_user.full_name if sender_user else None,
                } if sender_user else None,
                "recipient": {
                    "id": str(recipient_user.id) if recipient_user else None,
                    "username": recipient_user.username if recipient_user else None,
                    "wallet_address": recipient_user.wallet_address if recipient_user else None,
                    "full_name": recipient_user.full_name if recipient_user else None,
                } if recipient_user else None,
            }
            transactions.append(transaction_dict)
        
        return transactions
    
    async def get_transaction_analytics(
        self,
        user: User,
        db: Session,
        period: str = "30d"  # 7d, 30d, 90d, 1y
    ) -> Dict[str, Any]:
        """
        Get transaction analytics and insights
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get base query
            base_query = self._build_base_query(user, db)
            base_query = base_query.filter(Transaction.created_at >= start_date)
            
            # Total transactions
            total_transactions = base_query.count()
            
            # Sent transactions
            sent_query = base_query.filter(Transaction.sender_id == user.id)
            sent_transactions = sent_query.count()
            sent_amount = sent_query.with_entities(func.sum(Transaction.amount)).scalar() or Decimal("0")
            
            # Received transactions
            received_query = base_query.filter(Transaction.recipient_id == user.id)
            received_transactions = received_query.count()
            received_amount = received_query.with_entities(func.sum(Transaction.amount)).scalar() or Decimal("0")
            
            # Status breakdown
            status_breakdown = {}
            for status in ["pending", "confirmed", "failed"]:
                count = base_query.filter(Transaction.status == status).count()
                status_breakdown[status] = count
            
            # Currency breakdown
            currency_breakdown = {}
            currency_stats = base_query.with_entities(
                Transaction.currency_type,
                func.count(Transaction.id),
                func.sum(Transaction.amount)
            ).group_by(Transaction.currency_type).all()
            
            for currency, count, total_amount in currency_stats:
                currency_breakdown[currency] = {
                    "count": count,
                    "total_amount": str(total_amount or Decimal("0"))
                }
            
            # Daily transaction volume (last 7 days)
            daily_volume = []
            for i in range(7):
                date = end_date - timedelta(days=i)
                day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                day_count = base_query.filter(
                    and_(
                        Transaction.created_at >= day_start,
                        Transaction.created_at < day_end
                    )
                ).count()
                
                daily_volume.append({
                    "date": day_start.date().isoformat(),
                    "count": day_count
                })
            
            daily_volume.reverse()  # Oldest to newest
            
            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "summary": {
                    "total_transactions": total_transactions,
                    "sent_transactions": sent_transactions,
                    "received_transactions": received_transactions,
                    "sent_amount": str(sent_amount),
                    "received_amount": str(received_amount),
                    "net_amount": str(received_amount - sent_amount)
                },
                "status_breakdown": status_breakdown,
                "currency_breakdown": currency_breakdown,
                "daily_volume": daily_volume
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction analytics: {e}")
            return {
                "period": period,
                "error": "Failed to generate analytics"
            }
    
    async def export_transactions(
        self,
        user: User,
        db: Session,
        export_format: str = "csv",
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export transactions to CSV or PDF
        """
        try:
            export_id = str(uuid.uuid4())
            
            # Get all transactions (no pagination for export)
            query = self._build_base_query(user, db)
            
            if filters:
                query = self._apply_filters(query, filters)
            
            if search_query:
                query = self._apply_search(query, search_query)
            
            # Order by creation date
            query = query.order_by(desc(Transaction.created_at))
            
            results = query.all()
            transactions = self._transform_transaction_results(results)
            
            if export_format == "csv":
                export_data = self._generate_csv_export(transactions)
            else:
                export_data = self._generate_pdf_export(transactions)
            
            # Store export in cache
            self._export_cache[export_id] = {
                "data": export_data,
                "format": export_format,
                "created_at": datetime.now(timezone.utc),
                "transaction_count": len(transactions)
            }
            
            return {
                "export_id": export_id,
                "format": export_format,
                "transaction_count": len(transactions),
                "download_url": f"/api/v1/transactions/export/{export_id}"
            }
            
        except Exception as e:
            logger.error(f"Error exporting transactions: {e}")
            return {
                "error": "Failed to export transactions"
            }
    
    def _generate_csv_export(self, transactions: List[Dict[str, Any]]) -> str:
        """Generate CSV export data"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Transaction Hash", "Amount", "Currency", "Type", "Status",
            "Description", "Gas Fee", "Block Height", "Created At", "Updated At",
            "Sender Username", "Sender Address", "Recipient Username", "Recipient Address"
        ])
        
        # Write data
        for tx in transactions:
            writer.writerow([
                tx["id"],
                tx["transaction_hash"],
                tx["amount"],
                tx["currency_type"],
                tx["transaction_type"],
                tx["status"],
                tx["description"] or "",
                tx["gas_fee"] or "",
                tx["block_height"] or "",
                tx["created_at"],
                tx["updated_at"] or "",
                tx["sender"]["username"] if tx["sender"] else "",
                tx["sender"]["wallet_address"] if tx["sender"] else "",
                tx["recipient"]["username"] if tx["recipient"] else "",
                tx["recipient"]["wallet_address"] if tx["recipient"] else ""
            ])
        
        return output.getvalue()
    
    def _generate_pdf_export(self, transactions: List[Dict[str, Any]]) -> str:
        """Generate PDF export data (placeholder)"""
        # This would use reportlab to generate PDF
        # For now, return a placeholder
        return f"PDF export for {len(transactions)} transactions (placeholder)"
    
    def get_export(self, export_id: str) -> Optional[Dict[str, Any]]:
        """Get exported data by ID"""
        if export_id in self._export_cache:
            export_data = self._export_cache[export_id]
            
            # Check if export is expired (1 hour)
            if datetime.now(timezone.utc) - export_data["created_at"] > timedelta(hours=1):
                del self._export_cache[export_id]
                return None
            
            return export_data
        
        return None
    
    def cleanup_expired_exports(self):
        """Clean up expired exports"""
        current_time = datetime.now(timezone.utc)
        expired_ids = []
        
        for export_id, export_data in self._export_cache.items():
            if current_time - export_data["created_at"] > timedelta(hours=1):
                expired_ids.append(export_id)
        
        for export_id in expired_ids:
            del self._export_cache[export_id]
            logger.info(f"Cleaned up expired export: {export_id}")


# Global service instance
transaction_history_service = TransactionHistoryService()
