# -*- coding: utf-8 -*-
"""User role definitions shared across the AHDUNYI server."""

from enum import Enum


class UserRole(str, Enum):
    """Enumeration of all supported user roles.

    Inherits from ``str`` so SQLAlchemy can store the value directly
    as a VARCHAR without extra serialisation.
    """

    MANAGER = "manager"
    TEAM_LEADER = "team_leader"
    QA_SPECIALIST = "qa_specialist"
    ADMIN_SUPPORT = "admin_support"
    AUDITOR = "auditor"
