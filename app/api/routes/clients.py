from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import secrets

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import get_password_hash
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter()


def generate_intake_token() -> str:
    """Generate a secure random token for intake form URLs."""
    return secrets.token_urlsafe(16)


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client with unique intake form URL."""

    # Generate unique intake token
    intake_token = generate_intake_token()

    # Ensure token is unique
    while True:
        result = await db.execute(
            select(Client).where(Client.intake_token == intake_token)
        )
        if not result.scalar_one_or_none():
            break
        intake_token = generate_intake_token()

    client = Client(
        **client_data.model_dump(),
        intake_token=intake_token,
        owner_id=current_user.id,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    return client


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all clients for the current user."""
    result = await db.execute(
        select(Client)
        .where(Client.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Client.created_at.desc())
    )
    clients = result.scalars().all()
    return clients


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific client by ID."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a client."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    # Update fields
    for field, value in client_data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a client."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    await db.delete(client)
    await db.commit()

    return None


@router.get("/{client_id}/intake-url")
async def get_intake_url(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the unique intake form URL for a client."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    if not client.intake_token:
        # Generate token if missing (for existing clients)
        intake_token = generate_intake_token()
        client.intake_token = intake_token
        await db.commit()
        await db.refresh(client)

    # Build the intake URL
    base_url = settings.FRONTEND_URL or "http://localhost:8000"
    intake_url = f"{base_url}/intake/{client.intake_token}"

    return {
        "client_id": client.id,
        "business_name": client.business_name,
        "intake_url": intake_url,
        "intake_token": client.intake_token,
    }


@router.post("/{client_id}/set-password")
async def set_client_password(
    client_id: int,
    password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a password for client portal access."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    if not client.primary_contact_email:
        raise HTTPException(
            status_code=400,
            detail="Client must have a primary contact email before setting password"
        )

    # Hash and set password
    client.password_hash = get_password_hash(password)
    await db.commit()

    return {
        "message": "Password set successfully",
        "client_id": client.id,
        "login_url": f"{settings.FRONTEND_URL or 'http://localhost:8000'}/api/v1/client/login",
        "email": client.primary_contact_email,
    }


@router.post("/{client_id}/publer-accounts")
async def assign_publer_accounts(
    client_id: int,
    account_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign Publer account IDs to a client with validation.

    This endpoint validates that the account IDs exist in Publer
    and returns human-readable account names for verification.

    After adding client's social accounts in Publer dashboard,
    use this endpoint to link them to the client.
    """
    from app.services.publer import publer_service

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    # Use client's workspace or require it to be set
    workspace_id = client.publer_workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=400,
            detail="Client must have a Publer workspace ID configured. Please set publer_workspace_id for this client first."
        )

    # Validate account IDs exist in CLIENT'S Publer workspace
    print(f"🔍 Validating {len(account_ids)} Publer account IDs for client {client.business_name} in workspace {workspace_id}...")
    validation_results = await publer_service.validate_account_ids(account_ids, workspace_id=workspace_id)
    invalid_ids = [aid for aid, is_valid in validation_results.items() if not is_valid]

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Publer account IDs: {', '.join(invalid_ids)}. Please verify these accounts exist in the client's Publer workspace ({workspace_id})."
        )

    # Get account details for verification
    account_details = await publer_service.get_account_details(account_ids, workspace_id=workspace_id)

    # Assign Publer account IDs
    client.publer_account_ids = account_ids
    await db.commit()
    await db.refresh(client)

    print(f"✅ Assigned {len(account_ids)} Publer accounts to {client.business_name}")
    for aid, details in account_details.items():
        print(f"   - {details.get('display', 'Unknown Account')}")

    # Return success with account details for confirmation
    return {
        "message": f"✅ Assigned {len(account_ids)} Publer accounts to {client.business_name}",
        "client_id": client.id,
        "client_name": client.business_name,
        "publer_account_ids": account_ids,
        "accounts": [
            {
                "id": aid,
                "provider": details.get('provider'),
                "name": details.get('name'),
                "username": details.get('username'),
                "display": details.get('display'),
            }
            for aid, details in account_details.items()
        ],
        "verification": f"Posts will be published to: {', '.join([d.get('display', 'Unknown') for d in account_details.values()])}"
    }


@router.get("/{client_id}/publer-accounts")
async def get_publer_accounts(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Publer account IDs and details assigned to a client."""
    from app.services.publer import publer_service

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check ownership
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    workspace_id = client.publer_workspace_id
    account_ids = client.publer_account_ids or []

    # Get account details if IDs are assigned and workspace is configured
    accounts = []
    if account_ids and workspace_id:
        account_details = await publer_service.get_account_details(account_ids, workspace_id=workspace_id)
        accounts = [
            {
                "id": aid,
                "provider": details.get('provider'),
                "name": details.get('name'),
                "username": details.get('username'),
                "display": details.get('display'),
            }
            for aid, details in account_details.items()
        ]

    return {
        "client_id": client.id,
        "business_name": client.business_name,
        "publer_workspace_id": workspace_id,
        "publer_account_ids": account_ids,
        "account_count": len(account_ids),
        "accounts": accounts,
    }
