from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import Waitlist
from ..schemas import WaitlistCreate, WaitlistResponse, ApiResponse

router = APIRouter()


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    waitlist_entry: WaitlistCreate,
    db: Session = Depends(get_db)
):
    """
    Join the waitlist with name, surname, email, and country.
    If country is "Other", custom_country must be provided.
    """
    try:
        # Check if email already exists
        existing_entry = db.query(Waitlist).filter(Waitlist.email == waitlist_entry.email).first()
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered on waitlist"
            )
        
        # Validate that custom_country is provided if country is "Other"
        if waitlist_entry.country == "Other" and not waitlist_entry.custom_country:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="custom_country is required when country is 'Other'"
            )
        
        # Create waitlist entry
        db_waitlist = Waitlist(
            first_name=waitlist_entry.first_name,
            last_name=waitlist_entry.last_name,
            email=waitlist_entry.email,
            country=waitlist_entry.country,
            custom_country=waitlist_entry.custom_country if waitlist_entry.country == "Other" else None
        )
        
        db.add(db_waitlist)
        db.commit()
        db.refresh(db_waitlist)
        
        return ApiResponse(
            success=True,
            message="Successfully joined waitlist",
            data=WaitlistResponse.model_validate(db_waitlist).model_dump()
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered on waitlist"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining waitlist: {str(e)}"
        )


@router.get("/", response_model=ApiResponse)
async def get_waitlist_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get waitlist entries (for admin/internal use).
    Returns paginated list of waitlist entries.
    """
    entries = db.query(Waitlist).offset(skip).limit(limit).all()
    
    return ApiResponse(
        success=True,
        message="Waitlist entries retrieved successfully",
        data=[WaitlistResponse.model_validate(entry).model_dump() for entry in entries]
    )

