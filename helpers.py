import os
from datetime import datetime
from io import BytesIO

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


# =========================
# PRIORITY SCORING
# =========================
def calculate_priority(casualties, injured, trapped, damaged_buildings, road_status):
    score = 0

    score += casualties * 10
    score += injured * 3
    score += trapped * 15
    score += damaged_buildings

    if road_status == "Partially Blocked":
        score += 20

    elif road_status == "Blocked":
        score += 40

    if score >= 100:
        return score, "🔴 CRITICAL"

    elif score >= 60:
        return score, "🟠 SEVERE"

    elif score >= 30:
        return score, "🟡 MODERATE"

    else:
        return score, "🟢 LOW"


def get_marker_color(priority):
    if priority == "🔴 CRITICAL":
        return "red"

    elif priority == "🟠 SEVERE":
        return "orange"

    elif priority == "🟡 MODERATE":
        return "lightred"

    else:
        return "green"


# =========================
# VALIDATION
# =========================
def validate_alert(magnitude, epicenter, depth):
    errors = []

    if magnitude <= 0:
        errors.append("Magnitude must be greater than 0.")

    if not epicenter.strip():
        errors.append("Epicenter is required.")

    if depth < 0:
        errors.append("Depth cannot be negative.")

    return errors


def validate_incident_report(
    barangay,
    municipality,
    casualties,
    injured,
    trapped,
    damaged_buildings,
    remarks,
    uploaded_photos
):
    errors = []

    if not barangay.strip():
        errors.append("Barangay is required.")

    if not municipality.strip():
        errors.append("Municipality / City is required.")

    has_impact_data = (
        casualties > 0 or
        injured > 0 or
        trapped > 0 or
        damaged_buildings > 0
    )

    has_remarks = bool(remarks.strip())
    has_photos = uploaded_photos is not None and len(uploaded_photos) > 0

    if not has_impact_data and not has_remarks and not has_photos:
        errors.append(
            "Report must contain at least one impact detail, remark, or photo."
        )

    return errors


# =========================
# COMMAND RECOMMENDATIONS
# =========================
def generate_recommendations(priority):
    if priority == "🔴 CRITICAL":
        return [
            "Activate Incident Command Post (ICP)",
            "Deploy Quick Reaction Force (QRF)",
            "Deploy Search and Rescue Team",
            "Deploy Medical Team",
            "Request Engineering Assessment Team",
            "Coordinate with LGU/MDRRMO and Barangay Officials",
            "Prepare evacuation area and casualty collection point"
        ]

    elif priority == "🟠 SEVERE":
        return [
            "Deploy assessment team immediately",
            "Place QRF on high alert",
            "Prepare medical support",
            "Coordinate with MDRRMO",
            "Monitor road access and lifeline utilities"
        ]

    elif priority == "🟡 MODERATE":
        return [
            "Conduct rapid damage assessment",
            "Place response team on standby",
            "Monitor incoming reports",
            "Coordinate with barangay officials"
        ]

    else:
        return [
            "Continue monitoring",
            "Validate field report",
            "Await additional updates"
        ]


def show_recommendations(st, priority):
    for action in generate_recommendations(priority):
        st.write(f"✅ {action}")


# =========================
# SAFE PAGE NAVIGATION
# =========================
def go_to_page(st, page_name):
    st.session_state.pending_page = page_name


def reset_alert_form(st):
    st.session_state.alert_form_counter += 1
    st.session_state.pending_page = "Earthquake Alerts"


def reset_incident_form(st):
    st.session_state.incident_form_counter += 1
    st.session_state.current_latitude = 0.000000
    st.session_state.current_longitude = 0.000000
    st.session_state.pending_page = "Incident Reports"


# =========================
# GEOCODING
# =========================
def geocode_location(barangay, municipality):
    geolocator = Nominatim(
        user_agent="e-warps-capstone"
    )

    search_query = f"{barangay}, {municipality}, Philippines"

    try:
        location = geolocator.geocode(
            search_query,
            timeout=10
        )

        if location:
            return (
                float(location.latitude),
                float(location.longitude),
                location.address
            )

        return None, None, None

    except (GeocoderTimedOut, GeocoderServiceError):
        return None, None, None


# =========================
# SITREP TEXT
# =========================
def generate_sitrep_text(reports_df, alerts_df):
    now_text = datetime.now().strftime("%d %B %Y %H%MH")

    if reports_df.empty:
        return f"As of {now_text}, no incident reports have been recorded in E-WARPS."

    total_reports = len(reports_df)
    affected_areas = reports_df["Barangay"].nunique()
    total_casualties = int(reports_df["Casualties"].sum())
    total_injured = int(reports_df["Injured"].sum())
    total_trapped = int(reports_df["Trapped Persons"].sum())
    total_damaged = int(reports_df["Damaged Buildings"].sum())

    critical_count = len(
        reports_df[reports_df["Priority"] == "🔴 CRITICAL"]
    )

    severe_count = len(
        reports_df[reports_df["Priority"] == "🟠 SEVERE"]
    )

    moderate_count = len(
        reports_df[reports_df["Priority"] == "🟡 MODERATE"]
    )

    low_count = len(
        reports_df[reports_df["Priority"] == "🟢 LOW"]
    )

    sorted_df = reports_df.sort_values(
        by="Priority Score",
        ascending=False
    )

    top = sorted_df.iloc[0]

    if not alerts_df.empty:
        latest_alert = alerts_df.iloc[0]

        alert_text = (
            f"The latest recorded earthquake alert indicates a magnitude "
            f"{latest_alert['Magnitude']} earthquake with epicenter at "
            f"{latest_alert['Epicenter']} and depth of {latest_alert['Depth']} km."
        )

    else:
        alert_text = "No earthquake alert has been recorded in the system."

    incident_details = []

    for _, report in sorted_df.iterrows():
        detail = (
            f"- {report['Barangay']}, {report['Municipality / City']} | "
            f"Priority: {report['Priority']} | "
            f"Score: {report['Priority Score']} | "
            f"Casualties: {report['Casualties']} | "
            f"Injured: {report['Injured']} | "
            f"Trapped: {report['Trapped Persons']} | "
            f"Damaged Buildings: {report['Damaged Buildings']} | "
            f"Road Status: {report['Road Status']} | "
            f"Remarks: {report['Remarks']}"
        )

        incident_details.append(detail)

    incident_details_text = "\n".join(incident_details)

    sitrep = f"""
SITUATION REPORT

As of {now_text}, E-WARPS recorded {total_reports} incident report/s affecting {affected_areas} barangay/area/s.

{alert_text}

Current reported impact:
- Total casualties: {total_casualties}
- Total injured persons: {total_injured}
- Total trapped persons: {total_trapped}
- Total damaged buildings/structures: {total_damaged}

Priority classification:
- Critical areas: {critical_count}
- Severe areas: {severe_count}
- Moderate areas: {moderate_count}
- Low priority areas: {low_count}

Highest priority area:
The highest priority area is {top['Barangay']}, {top['Municipality / City']}, classified as {top['Priority']} with a priority score of {top['Priority Score']}.

Per-area incident details:
{incident_details_text}

Recommended command action:
Immediate attention should be given to the highest priority areas. For critical areas, the commander may consider activation of the Incident Command Post, deployment of QRF, SAR, medical teams, and engineering assessment teams, and coordination with LGU/MDRRMO and barangay officials.

This report is AI-assisted and intended to support command decision-making. Final approval and action remain under human command authority.
"""

    return sitrep.strip()


# =========================
# PDF PHOTO HELPER
# =========================
def create_pdf_image(image_path, max_width=230, max_height=170):
    if not os.path.exists(image_path):
        return None

    try:
        image_reader = ImageReader(image_path)
        original_width, original_height = image_reader.getSize()

        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale = min(width_ratio, height_ratio)

        final_width = original_width * scale
        final_height = original_height * scale

        return Image(
            image_path,
            width=final_width,
            height=final_height
        )

    except Exception:
        return None


# =========================
# SITREP PDF
# =========================
def generate_pdf_sitrep(
    sitrep_text,
    reports_df,
    photos_by_report=None,
    prepared_by="",
    prepared_role="",
    reviewed_by="",
    approved_by=""
):
    if photos_by_report is None:
        photos_by_report = {}

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        "E-WARPS Situation Report",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 8))

    meta_text = (
        f"Generated: {datetime.now().strftime('%d %B %Y %H%MH')}<br/>"
        f"Prepared By: {prepared_by if prepared_by else '____________________'}<br/>"
        f"Role/Designation: {prepared_role if prepared_role else '____________________'}"
    )

    elements.append(Paragraph(meta_text, styles["BodyText"]))
    elements.append(Spacer(1, 14))

    elements.append(
        Paragraph(
            "Narrative Situation Summary",
            styles["Heading2"]
        )
    )

    for line in sitrep_text.split("\n"):
        if line.strip() == "":
            elements.append(Spacer(1, 8))
        else:
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(
                Paragraph(safe_line, styles["BodyText"])
            )

    elements.append(Spacer(1, 16))

    if not reports_df.empty:
        sorted_reports_df = reports_df.sort_values(
            by="Priority Score",
            ascending=False
        )

        elements.append(
            Paragraph(
                "Incident Report Summary Table",
                styles["Heading2"]
            )
        )

        table_data = [
            [
                "Barangay",
                "City",
                "Casualties",
                "Injured",
                "Trapped",
                "Score",
                "Priority"
            ]
        ]

        for _, row in sorted_reports_df.iterrows():
            table_data.append(
                [
                    str(row["Barangay"]),
                    str(row["Municipality / City"]),
                    str(row["Casualties"]),
                    str(row["Injured"]),
                    str(row["Trapped Persons"]),
                    str(row["Priority Score"]),
                    str(row["Priority"])
                ]
            )

        table = Table(
            table_data,
            repeatRows=1
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 18))

        elements.append(
            Paragraph(
                "Incident Details and Photos",
                styles["Heading2"]
            )
        )

        for _, report in sorted_reports_df.iterrows():
            report_id = int(report["ID"])

            incident_title = (
                f"{report['Barangay']}, {report['Municipality / City']} "
                f"- {report['Priority']}"
            )

            elements.append(
                Paragraph(
                    incident_title,
                    styles["Heading3"]
                )
            )

            details_data = [
                ["Priority Score", str(report["Priority Score"])],
                ["Casualties", str(report["Casualties"])],
                ["Injured", str(report["Injured"])],
                ["Trapped Persons", str(report["Trapped Persons"])],
                ["Damaged Buildings", str(report["Damaged Buildings"])],
                ["Road Status", str(report["Road Status"])],
                ["Latitude", str(report["Latitude"])],
                ["Longitude", str(report["Longitude"])],
                ["Remarks", str(report["Remarks"])],
            ]

            details_table = Table(
                details_data,
                colWidths=[120, 350]
            )

            details_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )

            elements.append(details_table)
            elements.append(Spacer(1, 8))

            report_photos = photos_by_report.get(report_id, [])

            if report_photos:
                elements.append(
                    Paragraph(
                        "Attached Incident Photos:",
                        styles["BodyText"]
                    )
                )

                photo_cells = []
                current_row = []

                for photo in report_photos:
                    photo_path = photo.get("filepath")
                    photo_filename = photo.get("filename", "Incident Photo")

                    pdf_image = create_pdf_image(photo_path)

                    if pdf_image is not None:
                        photo_block = [
                            pdf_image,
                            Paragraph(
                                str(photo_filename),
                                styles["BodyText"]
                            )
                        ]

                        current_row.append(photo_block)

                        if len(current_row) == 2:
                            photo_cells.append(current_row)
                            current_row = []

                if current_row:
                    photo_cells.append(current_row)

                if photo_cells:
                    photo_table = Table(
                        photo_cells,
                        colWidths=[250, 250]
                    )

                    photo_table.setStyle(
                        TableStyle(
                            [
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )

                    elements.append(photo_table)

                else:
                    elements.append(
                        Paragraph(
                            "Photos were recorded but could not be loaded into the PDF.",
                            styles["BodyText"]
                        )
                    )

            else:
                elements.append(
                    Paragraph(
                        "No photos attached for this incident.",
                        styles["BodyText"]
                    )
                )

            elements.append(Spacer(1, 16))

    elements.append(Spacer(1, 30))

    signature_data = [
        ["Prepared By:", prepared_by if prepared_by else "________________________"],
        ["Reviewed By:", reviewed_by if reviewed_by else "________________________"],
        ["Approved By:", approved_by if approved_by else "________________________"],
    ]

    signature_table = Table(
        signature_data,
        colWidths=[100, 300]
    )

    signature_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )

    elements.append(signature_table)

    doc.build(elements)

    buffer.seek(0)
    return buffer


# =========================
# RESOURCE ALLOCATION
# =========================
def generate_resource_recommendation(reports_df, resources_df):
    if reports_df.empty:
        return "No incident reports available for resource allocation."

    if resources_df.empty:
        return (
            "No resources have been encoded. Add available QRF, medical, SAR, "
            "engineering, vehicles, and equipment first."
        )

    sorted_reports = reports_df.sort_values(
        by="Priority Score",
        ascending=False
    )

    output = []

    output.append("Suggested Resource Allocation:")
    output.append("")

    for _, report in sorted_reports.iterrows():
        output.append(
            f"{report['Barangay']} - {report['Priority']}"
        )

        if report["Priority"] == "🔴 CRITICAL":
            output.append(
                "- Prioritize deployment of QRF, SAR, medical team, engineering assessment team, and available transport."
            )

        elif report["Priority"] == "🟠 SEVERE":
            output.append(
                "- Deploy assessment team, prepare QRF, and coordinate medical support."
            )

        elif report["Priority"] == "🟡 MODERATE":
            output.append(
                "- Deploy assessment team if available and monitor situation."
            )

        else:
            output.append(
                "- Monitor and validate incoming reports."
            )

        output.append("")

    output.append("Available Resources:")

    for _, resource in resources_df.iterrows():
        output.append(
            f"- {resource['Resource']}: {resource['Quantity']} available"
        )

    return "\n".join(output)