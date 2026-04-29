"""POST /api/v1/contact - Enterprise inquiry form (no public email exposed)."""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr

from world_of_taxonomy.api.rate_guard import check_per_ip_rate
from world_of_taxonomy.webhook import send_webhook

router = APIRouter(prefix="/api/v1", tags=["contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Contact name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    email: str = Field(..., min_length=3, max_length=320, description="Contact email")
    message: str = Field(..., min_length=10, max_length=2000, description="Message")


class ContactResponse(BaseModel):
    status: str = "received"
    message: str = "Thank you for your inquiry. We will be in touch shortly."


@router.post("/contact", response_model=ContactResponse)
async def submit_contact(body: ContactRequest, request: Request):
    """Submit an enterprise inquiry or general contact form.

    Delivers the message via the configured webhook. No admin email
    is ever exposed to the client.

    Per-IP rate guard: 5/hour. Each submission fires a webhook to our
    notification destination; without this, a single IP could flood
    the operator inbox/Slack channel.
    """
    check_per_ip_rate("contact", request, max_per_window=5)

    # Fire webhook in background (don't block the response)
    asyncio.create_task(
        send_webhook(
            event="enterprise_inquiry",
            data={
                "name": body.name,
                "company": body.company,
                "email": body.email,
                "message": body.message,
            },
        )
    )

    return ContactResponse()
