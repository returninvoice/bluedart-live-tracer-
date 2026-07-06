from io import BytesIO

import pandas as pd


def create_excel_file(results):
    output = BytesIO()

    df = pd.DataFrame(results)

    column_names = {
        "airway_bill_no": "Airway Bill No",
        "status": "Status",
        "location": "Location",
        "date_time": "Date/Time",
        "remarks": "Remarks",
        "last_synced": "Last Synced",
    }

    df = df.rename(columns=column_names)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="BlueDart Dashboard")

    output.seek(0)
    return output