# -*- coding: utf-8 -*-
"""
Permission point definitions and role→permission matrix.

Design philosophy
-----------------
* Every controllable feature maps to ONE permission string.
* Roles are just named collections of permission points.
* To add a new role: add it to ``UserRole`` (roles.py) and add one entry
  to ``ROLE_PERMISSION_MATRIX`` below.  Frontend needs NO changes.
* To add a new feature: add a ``Permission`` constant and assign it to
  the relevant roles in the matrix.  Frontend guards read permissions
  dynamically.

Author : AHDUNYI
Version: 9.0.0
"""
from __future__ import annotations

from typing import Dict, List

from server.constants.roles import UserRole


# ---------------------------------------------------------------------------
# Permission points  (format: "domain:action")
# ---------------------------------------------------------------------------
class Permission:
    """Namespace of all permission-point string constants.

    Use string constants (not an Enum) so they serialise to JSON trivially
    and can be compared with a plain ``in`` check on the frontend.
    """

    # -- View permissions ---------------------------------------------------
    VIEW_DASHBOARD    = "view:dashboard"      # Basic work-bench (everyone)
    VIEW_SHADOW_AUDIT = "view:shadow_audit"   # Manager-only audit screen
    VIEW_TEAM_INSIGHT = "view:team_insight"   # Team statistics panel
    VIEW_SETTINGS     = "view:settings"       # System settings page
    VIEW_SOP          = "view:sop"            # SOP / standards pages
    VIEW_REALTIME     = "view:realtime"       # Real-time patrol monitor
    VIEW_VIOLATIONS   = "view:violations"     # Violation review page

    # -- Action permissions ------------------------------------------------
    ACTION_DISPATCH_TASK  = "action:dispatch_task"  # Dispatch audit tasks
    ACTION_UPDATE_ROLE    = "action:update_role"    # Change another user's role
    ACTION_COMPLETE_TASK  = "action:complete_task"  # Mark own task complete
    ACTION_LOG_ACTION     = "action:log_action"     # Write operation log


# ---------------------------------------------------------------------------
# Role metadata  (label + colour shown in the UI)
# ---------------------------------------------------------------------------
ROLE_META: Dict[str, Dict[str, str]] = {
    UserRole.MANAGER.value: {
        "label": "风控经理",
        "color": "red",
        "dashboard_view": "supervisor",   # which dashboard component to mount
    },
    UserRole.TEAM_LEADER.value: {
        "label": "组长",
        "color": "orange",
        "dashboard_view": "leader",
    },
    UserRole.QA_SPECIALIST.value: {
        "label": "质检专员",
        "color": "purple",
        "dashboard_view": "auditor",
    },
    UserRole.ADMIN_SUPPORT.value: {
        "label": "行政支持",
        "color": "cyan",
        "dashboard_view": "auditor",
    },
    UserRole.AUDITOR.value: {
        "label": "审核员",
        "color": "green",
        "dashboard_view": "auditor",
    },
}


# ---------------------------------------------------------------------------
# Role → Permission matrix
# ---------------------------------------------------------------------------
# To add a new role: add ONE entry here.  That's it.
# To add a new permission: add the constant above, then assign to roles.
# ---------------------------------------------------------------------------
ROLE_PERMISSION_MATRIX: Dict[str, List[str]] = {
    UserRole.MANAGER.value: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_SHADOW_AUDIT,
        Permission.VIEW_TEAM_INSIGHT,
        Permission.VIEW_SETTINGS,
        Permission.VIEW_SOP,
        Permission.VIEW_REALTIME,
        Permission.VIEW_VIOLATIONS,
        Permission.ACTION_DISPATCH_TASK,
        Permission.ACTION_UPDATE_ROLE,
        Permission.ACTION_COMPLETE_TASK,
        Permission.ACTION_LOG_ACTION,
    ],
    UserRole.TEAM_LEADER.value: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TEAM_INSIGHT,
        Permission.VIEW_SOP,
        Permission.VIEW_REALTIME,
        Permission.VIEW_VIOLATIONS,
        Permission.ACTION_DISPATCH_TASK,
        Permission.ACTION_COMPLETE_TASK,
        Permission.ACTION_LOG_ACTION,
    ],
    UserRole.QA_SPECIALIST.value: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_SOP,
        Permission.VIEW_REALTIME,
        Permission.VIEW_VIOLATIONS,
        Permission.ACTION_COMPLETE_TASK,
        Permission.ACTION_LOG_ACTION,
    ],
    UserRole.ADMIN_SUPPORT.value: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_SOP,
        Permission.VIEW_SETTINGS,
        Permission.ACTION_LOG_ACTION,
    ],
    UserRole.AUDITOR.value: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_SOP,
        Permission.VIEW_REALTIME,
        Permission.VIEW_VIOLATIONS,
        Permission.ACTION_COMPLETE_TASK,
        Permission.ACTION_LOG_ACTION,
    ],
}


def get_permissions_for_role(role: str) -> List[str]:
    """Return the list of permission strings for *role*.

    Falls back to an empty list for unknown roles so the system degrades
    gracefully when new roles are added to the DB before the matrix is
    updated.

    Args:
        role: Role value string, e.g. ``"manager"``.

    Returns:
        List of permission-point strings.
    """
    return ROLE_PERMISSION_MATRIX.get(role, [])


def get_role_meta(role: str) -> Dict[str, str]:
    """Return UI metadata dict for *role*.

    Args:
        role: Role value string.

    Returns:
        Dict with ``label``, ``color``, ``dashboard_view`` keys.
        Falls back to a safe default for unknown roles.
    """
    return ROLE_META.get(role, {
        "label": role,          # raw value as fallback label
        "color": "gray",
        "dashboard_view": "auditor",
    })
