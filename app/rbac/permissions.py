"""RBAC permission codes and role defaults."""
from typing import Final

# ─── All permission codes ──────────────────────────────────────
ALL_PERMISSIONS: Final[list[dict]] = [
    {"code": "users.manage",      "description": "Create, update, deactivate users"},
    {"code": "resumes.read",      "description": "View resume metadata"},
    {"code": "resumes.write",     "description": "Upload resumes"},
    {"code": "resumes.delete",    "description": "Soft-delete resumes"},
    {"code": "taxonomy.manage",   "description": "Create, update, delete skill taxonomy"},
    {"code": "taxonomy.read",     "description": "Read skill taxonomy"},
    {"code": "logs.view",         "description": "View audit logs"},
    {"code": "jd.write",          "description": "Create job descriptions"},
    {"code": "jd.read",           "description": "Read job descriptions"},
    {"code": "analysis.write",    "description": "Create analyses"},
    {"code": "results.read",      "description": "Read analysis results"},
]

# ─── Role default permissions ──────────────────────────────────
ROLE_DEFAULTS: Final[dict[str, set[str]]] = {
    "admin": {p["code"] for p in ALL_PERMISSIONS},   # admin gets everything
    "hr": {
        "jd.write",
        "jd.read",
        "resumes.read",
        "resumes.write",
        "analysis.write",
        "results.read",
        "taxonomy.read",
    },
}
