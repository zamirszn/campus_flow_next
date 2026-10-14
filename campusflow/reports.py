"""Reporting."""
from .tickets import CATEGORIES, PRIORITIES, STATUSES


def build_report(tickets):
    """Return counts by status, priority, and category, plus resolution rate."""
    by_status = {name: 0 for name in STATUSES}
    by_priority = {name: 0 for name in PRIORITIES}
    by_category = {name: 0 for name in CATEGORIES}

    for ticket in tickets:
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1
        by_category[ticket["category"]] += 1

    total = len(tickets)
    resolved = by_status["resolved"]
    unresolved = by_status["open"] + by_status["in_progress"]
    rate = (resolved / total * 100) if total else 0.0

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "unresolved": unresolved,
        "resolved": resolved,
        "resolution_rate": rate,
    }


def format_report(report):
    """Return a printable string with all report fields."""
    lines = [f"Total tickets: {report['total']}", ""]

    lines.append("By status:")
    lines += [f"  {name:<12}{count}" for name, count in report["by_status"].items()]

    lines.append("")
    lines.append("By priority:")
    lines += [f"  {name:<12}{count}" for name, count in report["by_priority"].items()]

    lines.append("")
    lines.append("By category:")
    lines += [f"  {name:<12}{count}" for name, count in report["by_category"].items()]

    lines.append("")
    lines.append(f"Unresolved (open + in_progress): {report['unresolved']}")
    lines.append(f"Resolved:                         {report['resolved']}")
    lines.append(f"Resolution rate:                 {report['resolution_rate']:.1f}%")

    return "\n".join(lines)