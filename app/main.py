from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv
import pandas as pd

from app.dashboard_store import (
    add_tracking_ids,
    clear_dashboard,
    delete_tracking_ids,
    get_dashboard,
    get_export_rows,
    get_limit_info,
    increment_api_calls,
    update_tracking_result,
)
from app.excel_export import create_excel_file
from app.scraper import parse_tracking_ids, track_single_id

# Environment variables load karne ke liye
load_dotenv()

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return jsonify(
        {
            "success": True,
            "rows": get_dashboard(),
            "limit": get_limit_info(),
        }
    )


@app.route("/add", methods=["POST"])
def add_manual_tracking_ids():
    data = request.get_json(silent=True) or {}
    tracking_text = data.get("tracking_ids", "")

    tracking_ids = parse_tracking_ids(tracking_text)
    add_tracking_ids(tracking_ids)

    return jsonify(
        {
            "success": True,
            "rows": get_dashboard(),
            "limit": get_limit_info(),
        }
    )


@app.route("/upload", methods=["POST"])
def upload_excel():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"success": False, "message": "Please select an Excel file."}), 400

    try:
        # Excel file ko read karna bina header ke
        df = pd.read_excel(uploaded_file, header=None)
        first_column = df.iloc[:, 0].dropna().astype(str).tolist()

        tracking_ids = []

        # Aapka naya aur improved validation logic
        for value in first_column:
            tracking_id = value.strip().replace(".0", "")

            # Sirf wahi IDs leni hain jo numeric hon aur length >= 8 ho
            if tracking_id.isdigit() and len(tracking_id) >= 8:
                tracking_ids.append(tracking_id)

        add_tracking_ids(tracking_ids)

        return jsonify(
            {
                "success": True,
                "rows": get_dashboard(),
                "limit": get_limit_info(),
                "message": f"{len(tracking_ids)} tracking numbers imported.",
            }
        )

    except Exception as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/sync", methods=["POST"])
def sync_tracking_ids():
    data = request.get_json(silent=True) or {}
    tracking_ids = data.get("tracking_ids", [])

    if not tracking_ids:
        return jsonify({"success": False, "message": "No tracking IDs selected."}), 400

    limit = get_limit_info()
    if len(tracking_ids) > limit["remaining"]:
        return jsonify(
            {
                "success": False,
                "message": f"API limit exceeded. Remaining calls: {limit['remaining']}.",
            }
        ) or 400

    synced_rows = []

    for tracking_id in tracking_ids:
        result = track_single_id(tracking_id)
        updated_row = update_tracking_result(tracking_id, result)
        if updated_row:
            synced_rows.append(updated_row)

    increment_api_calls(len(tracking_ids))

    return jsonify(
        {
            "success": True,
            "rows": get_dashboard(),
            "synced": synced_rows,
            "limit": get_limit_info(),
        }
    )


@app.route("/delete", methods=["POST"])
def delete_rows():
    data = request.get_json(silent=True) or {}
    tracking_ids = data.get("tracking_ids", [])

    delete_tracking_ids(tracking_ids)

    return jsonify(
        {
            "success": True,
            "rows": get_dashboard(),
            "limit": get_limit_info(),
        }
    )


@app.route("/clear", methods=["POST"])
def clear_rows():
    clear_dashboard()

    return jsonify(
        {
            "success": True,
            "rows": get_dashboard(),
            "limit": get_limit_info(),
        }
    )


@app.route("/download", methods=["GET"])
def download():
    rows = get_export_rows()

    if not rows:
        return jsonify({"success": False, "message": "No tracking data available."}), 400

    excel_file = create_excel_file(rows)

    return send_file(
        excel_file,
        as_attachment=True,
        download_name="bluedart_tracking_dashboard.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(debug=True)