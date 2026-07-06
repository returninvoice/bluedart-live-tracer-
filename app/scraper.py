import os
import re
from datetime import datetime

import requests


def parse_tracking_ids(raw_text):
    if not raw_text:
        return []

    tracking_ids = re.split(r"[\n,\s]+", raw_text.strip())
    cleaned_ids = []

    for tracking_id in tracking_ids:
        tracking_id = tracking_id.strip()
        if tracking_id and tracking_id not in cleaned_ids:
            cleaned_ids.append(tracking_id)

    return cleaned_ids


def get_address_location(shipment):
    status = shipment.get("status", {})
    location = status.get("location", {})
    address = location.get("address", {})

    city = address.get("addressLocality", "")
    state = address.get("addressRegion", "")
    country = address.get("countryCode", "")

    parts = [part for part in [city, state, country] if part]
    return ", ".join(parts) if parts else "-"


def normalize_dhl_response(tracking_id, payload):
    shipments = payload.get("shipments", [])

    if not shipments:
        return {
            "airway_bill_no": tracking_id,
            "status": "No shipment found",
            "location": "-",
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remarks": "DHL API did not return shipment data for this tracking number.",
        }

    shipment = shipments[0]
    status_data = shipment.get("status", {})

    status = (
        status_data.get("description")
        or status_data.get("status")
        or status_data.get("statusCode")
        or "Status not found"
    )

    date_time = (
        status_data.get("timestamp")
        or shipment.get("estimatedTimeOfDelivery")
        or "-"
    )

    service = shipment.get("service") or "bluedart"

    return {
        "airway_bill_no": shipment.get("id") or tracking_id,
        "status": status,
        "location": get_address_location(shipment),
        "date_time": date_time,
        "remarks": service,
    }


def track_single_id(tracking_id):
    api_url = os.getenv("BLUEDART_TRACKING_API_URL")
    api_key = os.getenv("BLUEDART_API_KEY")

    if not api_url or not api_key:
        return {
            "airway_bill_no": tracking_id,
            "status": "API not configured",
            "location": "-",
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remarks": "Add DHL API URL and API key in .env file.",
        }

    headers = {
        "Accept": "application/json",
        "DHL-API-Key": api_key,
    }

    try:
        response = requests.get(
            api_url,
            params={"trackingNumber": tracking_id},
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()
        payload = response.json()

        return normalize_dhl_response(tracking_id, payload)

    except requests.exceptions.RequestException as error:
        return {
            "airway_bill_no": tracking_id,
            "status": "Request failed",
            "location": "-",
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remarks": str(error),
        }

    except ValueError:
        return {
            "airway_bill_no": tracking_id,
            "status": "Invalid JSON",
            "location": "-",
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remarks": "API response was not valid JSON.",
        }