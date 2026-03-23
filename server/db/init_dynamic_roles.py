# -*- coding: utf-8 -*-
"""
Initialize dynamic roles and permissions from existing hardcoded configuration.

This script migrates the hardcoded role and permission definitions from
server/constants/roles.py and server/constants/permissions.py into the
new dynamic database tables.

Author : AHDUNYI
Version: 9.1.0
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session
from server.core.database import engine
from server.db.models_extended import DynamicRole, Permission, RolePermission
from server.constants.roles import UserRole
from server.constants.permissions import ROLE_META, ROLE_PERMISSION_MATRIX, Permission as PermEnum


def migrate_existing_roles(session: Session) -> dict:
    """Migrate existing hardcoded roles to dynamic_roles table.
    
    Returns:
        Dictionary mapping old role values to new role IDs.
    """
    role_mapping = {}
    
    for role_enum in UserRole:
        role_value = role_enum.value
        meta = ROLE_META.get(role_value, {})
        
        # Check if role already exists
        existing_role = session.query(DynamicRole).filter_by(name=role_value).first()
        if existing_role:
            print(f"✓ Role '{role_value}' already exists (ID: {existing_role.id})")
            role_mapping[role_value] = existing_role.id
            continue
        
        # Create new dynamic role
        new_role = DynamicRole(
            name=role_value,
            display_name=meta.get("label", role_value.title().replace("_", " ")),
            description=f"System role: {role_value}",
            color=meta.get("color", "#1890ff"),
            dashboard_view=meta.get("dashboard_view", "auditor"),
            is_system=True,
            is_active=True
        )
        
        session.add(new_role)
        session.flush()  # Get the ID
        
        print(f"✓ Created role '{role_value}' (ID: {new_role.id})")
        role_mapping[role_value] = new_role.id
    
    session.commit()
    return role_mapping


def migrate_existing_permissions(session: Session) -> dict:
    """Migrate existing hardcoded permissions to permissions table.
    
    Returns:
        Dictionary mapping permission codes to permission IDs.
    """
    permission_mapping = {}
    
    # Get all permission enums
    for perm_enum in PermEnum:
        perm_code = perm_enum.value
        
        # Check if permission already exists
        existing_perm = session.query(Permission).filter_by(code=perm_code).first()
        if existing_perm:
            print(f"✓ Permission '{perm_code}' already exists (ID: {existing_perm.id})")
            permission_mapping[perm_code] = existing_perm.id
            continue
        
        # Parse permission code to get name and category
        parts = perm_code.split(":")
        if len(parts) == 2:
            category, action = parts
            name = f"{action.replace('_', ' ').title()} {category.title()}"
        else:
            category = "general"
            name = perm_code.replace("_", " ").title()
        
        # Create new permission
        new_perm = Permission(
            code=perm_code,
            name=name,
            category=category,
            description=f"System permission: {perm_code}",
            is_system=True,
            is_active=True
        )
        
        session.add(new_perm)
        session.flush()  # Get the ID
        
        print(f"✓ Created permission '{perm_code}' (ID: {new_perm.id})")
        permission_mapping[perm_code] = new_perm.id
    
    session.commit()
    return permission_mapping


def migrate_role_permissions(session: Session, role_mapping: dict, permission_mapping: dict):
    """Migrate existing role-permission relationships."""
    
    for role_value, perm_codes in ROLE_PERMISSION_MATRIX.items():
        role_id = role_mapping.get(role_value)
        if not role_id:
            print(f"⚠ Warning: Role '{role_value}' not found in mapping")
            continue
        
        for perm_code in perm_codes:
            perm_id = permission_mapping.get(perm_code)
            if not perm_id:
                print(f"⚠ Warning: Permission '{perm_code}' not found in mapping")
                continue
            
            # Check if relationship already exists
            existing = session.query(RolePermission).filter_by(
                role_id=role_id,
                permission_id=perm_id
            ).first()
            
            if existing:
                continue
            
            # Create new relationship
            new_rel = RolePermission(
                role_id=role_id,
                permission_id=perm_id
            )
            session.add(new_rel)
    
    session.commit()
    print("✓ Migrated role-permission relationships")


def update_user_roles(session: Session, role_mapping: dict):
    """Update existing users to use new role IDs."""
    from server.db.models import User
    
    users = session.query(User).all()
    updated_count = 0
    
    for user in users:
        # Get the old role value from the enum (if still accessible)
        # Since we changed the model, we need to handle this differently
        # For now, we'll skip this step and handle it in a separate migration
        pass
    
    print(f"✓ Updated {updated_count} users")
    return updated_count


def main():
    """Main migration function."""
    print("=" * 60)
    print("Dynamic Roles & Permissions Migration")
    print("=" * 60)
    
    with Session(engine) as session:
        try:
            # Step 1: Migrate roles
            print("\n1. Migrating roles...")
            role_mapping = migrate_existing_roles(session)
            
            # Step 2: Migrate permissions
            print("\n2. Migrating permissions...")
            permission_mapping = migrate_existing_permissions(session)
            
            # Step 3: Migrate role-permission relationships
            print("\n3. Migrating role-permission relationships...")
            migrate_role_permissions(session, role_mapping, permission_mapping)
            
            # Step 4: Update users (to be done after full migration)
            # print("\n4. Updating user roles...")
            # update_user_roles(session, role_mapping)
            
            print("\n" + "=" * 60)
            print("Migration completed successfully!")
            print("=" * 60)
            
            # Print summary
            print(f"\nSummary:")
            print(f"  - Roles migrated: {len(role_mapping)}")
            print(f"  - Permissions migrated: {len(permission_mapping)}")
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()