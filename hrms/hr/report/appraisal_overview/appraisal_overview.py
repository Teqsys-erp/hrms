# Path -hrms/hr/report/appraisal_overview/appraisal_overview.py
import frappe
from frappe import _

def execute(filters: dict | None = None) -> tuple:
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data, rating_summary = get_data(filters)

    chart = get_rating_distribution_chart(rating_summary)


    return columns, data, None, chart

def get_columns() -> list[dict]:
    return [
        {"fieldname": "employee", "fieldtype": "Link", "label": _("Employee"), "options": "Employee", "width": 100},
        {"fieldname": "employee_name", "fieldtype": "Data", "label": _("Employee Name"), "width": 0},
        {"fieldname": "designation", "fieldtype": "Link", "label": _("Designation"), "options": "Designation", "width": 100},
        {"fieldname": "appraisal_cycle", "fieldtype": "Link", "label": _("Appraisal Cycle"), "options": "Appraisal Cycle", "width": 100},
        {"fieldname": "appraisal", "fieldtype": "Link", "label": _("Appraisal"), "options": "Appraisal", "width": 0},
        {"fieldname": "feedback_count", "fieldtype": "Int", "label": _("Feedback Count"), "width": 0},
        {"fieldname": "avg_feedback_score", "fieldtype": "Float", "label": _("Avg Feedback Score"), "width": 0},
        {"fieldname": "goal_score", "fieldtype": "Float", "label": _("Goal Score"), "width": 0},
        {"fieldname": "self_score", "fieldtype": "Float", "label": _("Self Score"), "width": 0},
        {"fieldname": "final_score", "fieldtype": "Float", "label": _("Final Score"), "width": 0},
        {"fieldname": "rating", "fieldtype": "Data", "label": _("Rating"), "width": 80},
        {"fieldname": "department", "fieldtype": "Link", "label": _("Department"), "options": "Department", "width": 150},
    ]

def get_data(filters: dict | None = None) -> tuple[list[dict], dict]:
    Appraisal = frappe.qb.DocType("Appraisal")
    query = (
        frappe.qb.from_(Appraisal)
        .select(
            Appraisal.employee,
            Appraisal.employee_name,
            Appraisal.designation,
            Appraisal.department,
            Appraisal.appraisal_cycle,
            Appraisal.name.as_("appraisal"),
            Appraisal.avg_feedback_score,
            Appraisal.total_score.as_("goal_score"),
            Appraisal.self_score,
            Appraisal.final_score,
        )
        .where(Appraisal.docstatus != 2)
    )

    for condition in ["appraisal_cycle", "employee", "department", "designation", "company"]:
        if filters.get(condition):
            query = query.where(Appraisal[condition] == filters.get(condition))

    query = query.orderby(Appraisal.appraisal_cycle)
    query = query.orderby(Appraisal.final_score, order=frappe.qb.desc)
    appraisals = query.run(as_dict=True)

    rating_summary = {}

    for row in appraisals:
        row["feedback_count"] = frappe.db.count(
            "Employee Performance Feedback", {"appraisal": row.appraisal, "docstatus": 1}
        )

        # Assign rating based on final score
        if 4 <= row["final_score"] <= 5:
            row["rating"] = "A"
        elif 3 <= row["final_score"] < 4:
            row["rating"] = "B+"
        elif 2 <= row["final_score"] < 3:
            row["rating"] = "B"
        elif 1 <= row["final_score"] < 2:
            row["rating"] = "C"
        else:
            row["rating"] = "D"

        # Build rating summary count
        rating_summary.setdefault(row["rating"], 0)
        rating_summary[row["rating"]] += 1

    return appraisals, rating_summary


def get_rating_distribution_chart(rating_summary: dict) -> dict:
    # Maintain order in the bar chart
    ratings_order = ["A", "B+", "B", "C", "D"]
    labels = []
    values = []

    for rating in ratings_order:
        labels.append(rating)
        values.append(rating_summary.get(rating, 0))

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Employee Count"),
                    "values": values,
                }
            ],
        },
        "type": "donut",
        "height": 250,
    }
