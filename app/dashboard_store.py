from datetime import datetime

API_DAILY_LIMIT = 250

dashboard_rows = []
api_calls_used = 0


def get_dashboard():
    return dashboard_rows


def get_limit_info():
    remaining = max(API_DAILY_LIMIT - api_calls_used, 0)

    return {
        "daily_limit": API_DAILY_LIMIT,
        "used": api_calls_used,
        "remaining": remaining,
    }


def add_tracking_ids(tracking_ids):
    existing_ids = {row["airway_bill_no"] for row in dashboard_rows}

    for tracking_id in tracking_ids:
        if tracking_id not in existing_ids:
            dashboard_rows.append(
                {
                    "airway_bill_no": tracking_id,
                    "status": "Not synced",
                    "location": "-",
                    "date_time": "-",
                    "remarks": "Waiting for sync.",
                    "last_synced": "-",
                }
            )


def update_tracking_result(tracking_id, result):
    for row in dashboard_rows:
        if row["airway_bill_no"] == tracking_id:
            row["status"] = result.get("status", "-")
            row["location"] = result.get("location", "-")
            row["date_time"] = result.get("date_time", "-")
            row["remarks"] = result.get("remarks", "-")
            row["last_synced"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return row

    return None


def increment_api_calls(count):
    global api_calls_used
    api_calls_used += count


def delete_tracking_ids(tracking_ids):
    global dashboard_rows

    tracking_id_set = set(tracking_ids)
    dashboard_rows = [
        row for row in dashboard_rows
        if row["airway_bill_no"] not in tracking_id_set
    ]


def clear_dashboard():
    global dashboard_rows
    dashboard_rows = []


def get_export_rows():
    return dashboard_rows