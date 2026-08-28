"""
tests/test_integration_rbac.py - Integration test: end-to-end UI + RBAC.

Simulates login for each role and verifies:
1. Sidebar shows only modules the role can access.
2. Navigating to each allowed module works.
3. Navigating to a denied module raises PermissionError.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from database.database import initialize_database, DB_PATH
from auth.authentication import register_user, authenticate_user


ALL_MODULES = ["dashboard", "cases", "evidence", "custody",
               "reports", "audit", "users"]


def setup_roles_and_users() -> None:
    """Initialize DB and create one user per role."""
    initialize_database()
    register_user("admin", "Admin@123", "ADMINISTRATOR")
    register_user("aud", "AudPass123!", "AUDITOR")
    register_user("cust", "CustPass123!", "EVIDENCE CUSTODIAN")
    register_user("inv", "InvPass123!", "CASE INVESTIGATOR")
    register_user("analyst", "Analyst123!", "FORENSIC ANALYST")


def test_role_simulation(username, password, label, expected_visible):
    """Login as the role, then verify sidebar contents and navigation perms."""
    from app import DigitalForensicsApp
    from auth.authorization import PERMISSIONS_ALL, DEFAULT_ROLE_PERMISSIONS

    root = tk.Tk()
    root.withdraw()
    try:
        app = DigitalForensicsApp(root)
        user, sess = authenticate_user(username, password)
        app._on_login_success(user, sess)
        visible = set(app._sidebar_buttons.keys())

        print(f"\n[{label}]")
        print(f"  Sidebar visible: {sorted(visible)}")
        print(f"  Expected visible: {sorted(expected_visible)}")
        if visible != expected_visible:
            missing = expected_visible - visible
            extra = visible - expected_visible
            if missing:
                print(f"  FAIL: missing modules: {missing}")
            if extra:
                print(f"  FAIL: extra modules: {extra}")
            raise AssertionError(f"{label} sidebar mismatch")

        # Try navigating to each module
        perms = frozenset(user["permissions"])
        for m in ALL_MODULES:
            # Each module's required permission (matches app.py SIDEBAR_MODULES)
            required = {
                "dashboard": "case.view",
                "cases": "case.view",
                "evidence": "evidence.view",
                "custody": "custody.view",
                "reports": "report.generate",
                "audit": "audit.view",
                "users": "user.view",
            }.get(m)
            should_allow = required in perms

            # Test the permission check directly (avoiding messagebox dialogs)
            if should_allow:
                try:
                    app._require(perms, required)
                    print(f"    [OK]   {m} (perm {required!r} granted)")
                except PermissionError as e:
                    print(f"    [BUG]  {m}: should be allowed but raised {e}")
                    raise
            else:
                try:
                    app._require(perms, required)
                    print(f"    [BUG]  {m}: perm {required!r} should have raised")
                    raise AssertionError(f"{label} has {required!r} but shouldn't")
                except PermissionError:
                    print(f"    [OK]   {m} (perm {required!r} correctly denied)")
        return True
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def main() -> int:
    print("=" * 70)
    print("DIGITAL FORENSICS - UI/RBAC INTEGRATION TEST")
    print("=" * 70)

    # Reset DB
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError:
            pass
    for ext in ("-wal", "-shm"):
        p = Path(str(DB_PATH) + ext)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    setup_roles_and_users()

    test_role_simulation(
        "admin", "Admin@123", "ADMINISTRATOR",
        {"dashboard", "cases", "evidence", "custody",
         "reports", "audit", "users"},
    )
    test_role_simulation(
        "aud", "AudPass123!", "AUDITOR",
        {"dashboard", "cases", "evidence", "custody",
         "reports", "audit"},  # no user mgmt
    )
    test_role_simulation(
        "cust", "CustPass123!", "EVIDENCE CUSTODIAN",
        {"dashboard", "cases", "evidence", "custody"},
    )
    test_role_simulation(
        "inv", "InvPass123!", "CASE INVESTIGATOR",
        {"dashboard", "cases", "evidence", "custody", "reports"},
    )
    test_role_simulation(
        "analyst", "Analyst123!", "FORENSIC ANALYST",
        {"dashboard", "cases", "evidence", "custody"},
    )

    print()
    print("=" * 70)
    print("ALL UI/RBAC INTEGRATION TESTS PASSED")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
