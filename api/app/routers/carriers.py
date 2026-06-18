import asyncio
import re

import httpx
from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.config import settings
from app.schemas import CarrierVerifyRequest, CarrierVerifyResponse

router = APIRouter(prefix="/carriers", tags=["carriers"], dependencies=[Depends(verify_api_key)])

# FMCSA's API is a real government service with no uptime SLA -- it occasionally
# returns transient 5xx errors or times out. Retrying a couple of times with a
# short delay turns most of these blips into successful lookups instead of
# telling the carrier "sorry, our systems are down" on the first hiccup.
FMCSA_MAX_ATTEMPTS = 3
FMCSA_RETRY_DELAY_SECONDS = 1.0


def _clean_mc_number(raw: str) -> str:
    """
    Carriers say things like "MC 123456" or "my MC number is one two three four
    five six" -> by the time the agent sends it to us it should already be digits,
    but we strip any non-digit characters here as a safety net.
    """
    return re.sub(r"\D", "", raw)


@router.post("/verify", response_model=CarrierVerifyResponse)
async def verify_carrier(request: CarrierVerifyRequest):
    """
    Looks up a carrier's operating authority by MC (docket) number using FMCSA's
    free QCMobile API. This is the very first thing the agent does on every call,
    before it offers any load details.

    If no FMCSA_WEBKEY is configured, falls back to a mock response so local
    development never gets blocked waiting on FMCSA signup -- this is intentional,
    not a bug, and worth mentioning if you're asked about it.
    """
    mc_number = _clean_mc_number(request.mc_number)

    if not settings.FMCSA_WEBKEY:
        return CarrierVerifyResponse(
            mc_number=mc_number,
            eligible=True,
            carrier_name="Mock Carrier (no FMCSA key configured)",
            reason="FMCSA_WEBKEY not set -- returning mock eligible=True for local testing",
        )

    url = f"{settings.FMCSA_BASE_URL}/docket-number/{mc_number}"

    last_status = None
    for attempt in range(1, FMCSA_MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params={"webKey": settings.FMCSA_WEBKEY})
        except httpx.HTTPError:
            # Network-level failure (timeout, connection reset, etc.) -- treat
            # like a failed attempt and retry rather than crashing the call.
            last_status = "network_error"
        else:
            if resp.status_code == 200:
                data = resp.json()
                # FMCSA's response shape nests the carrier record inside a "content" list.
                # Defensive parsing because government API responses are not always
                # perfectly consistent, and we'd rather fail safe than crash the call.
                return _parse_fmcsa_response(data, mc_number)
            last_status = resp.status_code

        if attempt < FMCSA_MAX_ATTEMPTS:
            await asyncio.sleep(FMCSA_RETRY_DELAY_SECONDS)

    return CarrierVerifyResponse(
        mc_number=mc_number,
        eligible=False,
        reason=f"FMCSA lookup failed after {FMCSA_MAX_ATTEMPTS} attempts (last status: {last_status})",
    )


def _parse_fmcsa_response(data: dict, mc_number: str) -> CarrierVerifyResponse:
    """
    Separated from the HTTP call so it can be unit tested directly against a
    real captured FMCSA response, with no network call involved.

    Confirmed against a real response (Greyhound Lines, DOT 44110, fetched
    2026-06-17): the field is "allowedToOperate" (not "allowToOperate" as
    FMCSA's own docs page claims), and there is no simple boolean
    out-of-service flag -- instead "oosDate" is null when the carrier is
    in good standing and holds a date string when it isn't.
    """
    carriers = data.get("content") or []
    if not carriers:
        return CarrierVerifyResponse(
            mc_number=mc_number,
            eligible=False,
            reason="No carrier found for this MC number",
        )

    carrier = carriers[0].get("carrier", carriers[0])

    allowed = str(carrier.get("allowedToOperate", "N")).upper() == "Y"
    oos_date = carrier.get("oosDate")
    eligible = allowed and not oos_date

    if eligible:
        reason = None
    elif not allowed:
        reason = "Carrier is not currently authorized to operate (allowedToOperate=N)"
    else:
        reason = f"Carrier was placed out of service on {oos_date}"

    return CarrierVerifyResponse(
        mc_number=mc_number,
        eligible=eligible,
        carrier_name=carrier.get("legalName"),
        reason=reason,
    )
