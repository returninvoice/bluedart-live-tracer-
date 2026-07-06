const excelFile = document.getElementById("excelFile");
const uploadBtn = document.getElementById("uploadBtn");
const trackingIds = document.getElementById("trackingIds");
const addBtn = document.getElementById("addBtn");
const selectAll = document.getElementById("selectAll");
const syncSelectedBtn = document.getElementById("syncSelectedBtn");
const syncAllBtn = document.getElementById("syncAllBtn");
const deleteSelectedBtn = document.getElementById("deleteSelectedBtn");
const clearBtn = document.getElementById("clearBtn");
const downloadBtn = document.getElementById("downloadBtn");
const dashboardBody = document.getElementById("dashboardBody");
const message = document.getElementById("message");
const remainingCalls = document.getElementById("remainingCalls");
const limitText = document.getElementById("limitText");

let dashboardRows = [];

function setMessage(text, isError = false) {
    message.textContent = text;
    message.className = isError ? "message error" : "message";
}

function updateLimit(limit) {
    if (!limit) return;

    remainingCalls.textContent = limit.remaining;
    limitText.textContent = `${limit.used} used / ${limit.daily_limit} daily`;
}

function renderDashboard(rows) {
    dashboardRows = rows || [];
    dashboardBody.innerHTML = "";

    if (!dashboardRows.length) {
        dashboardBody.innerHTML = `<tr><td colspan="8" class="empty">No tracking numbers added yet.</td></tr>`;
        selectAll.checked = false;
        return;
    }

    dashboardRows.forEach((row) => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>
                <input class="row-check" type="checkbox" value="${row.airway_bill_no}">
            </td>
            <td class="awb">${row.airway_bill_no}</td>
            <td><span class="status">${row.status || "-"}</span></td>
            <td>${row.location || "-"}</td>
            <td>${row.date_time || "-"}</td>
            <td>${row.remarks || "-"}</td>
            <td>${row.last_synced || "-"}</td>
            <td>
                <button class="small sync-one" type="button" data-id="${row.airway_bill_no}">Sync</button>
                <button class="small danger delete-one" type="button" data-id="${row.airway_bill_no}">Delete</button>
            </td>
        `;

        dashboardBody.appendChild(tr);
    });
}

function getSelectedIds() {
    return Array.from(document.querySelectorAll(".row-check:checked")).map(
        (checkbox) => checkbox.value
    );
}

async function refreshDashboard() {
    const response = await fetch("/dashboard");
    const data = await response.json();

    if (data.success) {
        renderDashboard(data.rows);
        updateLimit(data.limit);
    }
}

async function syncIds(ids) {
    if (!ids.length) {
        setMessage("Please select at least one tracking number.", true);
        return;
    }

    setMessage(`Syncing ${ids.length} tracking number(s)...`);

    const response = await fetch("/sync", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ tracking_ids: ids }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        setMessage(data.message || "Sync failed.", true);
        return;
    }

    renderDashboard(data.rows);
    updateLimit(data.limit);
    setMessage("Sync completed.");
}

async function deleteIds(ids) {
    if (!ids.length) {
        setMessage("Please select at least one tracking number.", true);
        return;
    }

    const response = await fetch("/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ tracking_ids: ids }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        setMessage("Delete failed.", true);
        return;
    }

    renderDashboard(data.rows);
    updateLimit(data.limit);
    setMessage("Selected tracking numbers deleted.");
}

uploadBtn.addEventListener("click", async () => {
    if (!excelFile.files.length) {
        setMessage("Please select an Excel file first.", true);
        return;
    }

    const formData = new FormData();
    formData.append("file", excelFile.files[0]);

    setMessage("Uploading Excel file...");

    const response = await fetch("/upload", {
        method: "POST",
        body: formData,
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        setMessage(data.message || "Upload failed.", true);
        return;
    }

    renderDashboard(data.rows);
    updateLimit(data.limit);
    setMessage(data.message || "Excel uploaded.");
});

addBtn.addEventListener("click", async () => {
    const text = trackingIds.value.trim();

    if (!text) {
        setMessage("Please enter tracking IDs.", true);
        return;
    }

    const response = await fetch("/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ tracking_ids: text }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
        setMessage("Unable to add tracking IDs.", true);
        return;
    }

    renderDashboard(data.rows);
    updateLimit(data.limit);
    trackingIds.value = "";
    setMessage("Tracking IDs added to dashboard.");
});

selectAll.addEventListener("change", () => {
    document.querySelectorAll(".row-check").forEach((checkbox) => {
        checkbox.checked = selectAll.checked;
    });
});

syncSelectedBtn.addEventListener("click", () => {
    syncIds(getSelectedIds());
});

syncAllBtn.addEventListener("click", () => {
    const allIds = dashboardRows.map((row) => row.airway_bill_no);
    syncIds(allIds);
});

deleteSelectedBtn.addEventListener("click", () => {
    deleteIds(getSelectedIds());
});

clearBtn.addEventListener("click", async () => {
    const response = await fetch("/clear", {
        method: "POST",
    });

    const data = await response.json();

    if (data.success) {
        renderDashboard(data.rows);
        updateLimit(data.limit);
        setMessage("Dashboard cleared.");
    }
});

downloadBtn.addEventListener("click", () => {
    window.location.href = "/download";
});

dashboardBody.addEventListener("click", (event) => {
    const syncButton = event.target.closest(".sync-one");
    const deleteButton = event.target.closest(".delete-one");

    if (syncButton) {
        syncIds([syncButton.dataset.id]);
    }

    if (deleteButton) {
        deleteIds([deleteButton.dataset.id]);
    }
});

refreshDashboard();