# -*- coding: utf-8 -*-
"""
Dynamic role and permission management API.

Provides endpoints for administrators to:
1. Create, read, update, delete dynamic roles
2. Manage permission definitions
3. Configure role-permission relationships
4. Get role and permission catalogues

Author : AHDUNYI
Version: 9.1.0
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.api.auth import get_current_user
from server.core.database import get_db
from server.db.models import User
from server.db.models_extended import DynamicRole, Permission, RolePermission

router = APIRouter(prefix="/dynamic-roles", tags=["dynamic-roles"])


# ============================================================================
# Pydantic Schemas
# ============================================================================


class PermissionSchema(BaseModel):
    """Permission schema for API responses."""

    id: int
    code: str
    name: str
    category: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class RoleSchema(BaseModel):
    """Role schema for API responses."""

    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    color: str
    dashboard_view: str
    is_system: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    permissions: List[PermissionSchema] = []

    class Config:
        from_attributes = True


class RoleCreateSchema(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z_]+$")
    display_name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field("#1890ff", pattern=r"^#[0-9a-fA-F]{6}$")
    dashboard_view: str = Field("auditor", max_length=64)
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""

    display_name: Optional[str] = Field(None, min_length=2, max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    dashboard_view: Optional[str] = Field(None, max_length=64)
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class PermissionCreate(BaseModel):
    """Schema for creating a new permission."""

    code: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-z_:]+$")
    name: str = Field(..., min_length=3, max_length=128)
    category: str = Field("general", max_length=64)
    description: Optional[str] = Field(None, max_length=500)


class PermissionUpdate(BaseModel):
    """Schema for updating an existing permission."""

    name: Optional[str] = Field(None, min_length=3, max_length=128)
    category: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RolePermissionUpdate(BaseModel):
    """Schema for updating role-permission relationships."""

    role_id: int
    permission_ids: List[int]


# ============================================================================
# Helper Functions
# ============================================================================


def _check_admin_permission(current_user: User) -> None:
    """Check if current user has admin permissions."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required.",
        )


def _get_role_or_404(db: Session, role_id: int) -> DynamicRole:
    """Get role by ID or raise 404."""
    role = db.query(DynamicRole).filter(DynamicRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found.",
        )
    return role


def _get_permission_or_404(db: Session, permission_id: int) -> Permission:
    """Get permission by ID or raise 404."""
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found.",
        )
    return permission


def _validate_permission_ids(
    db: Session, permission_ids: List[int]
) -> List[Permission]:
    """Validate that all permission IDs exist and return permission objects."""
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()

    if len(permissions) != len(permission_ids):
        found_ids = {p.id for p in permissions}
        missing_ids = set(permission_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission IDs: {missing_ids}",
        )

    return permissions


# ============================================================================
# Role Endpoints
# ============================================================================


@router.get("/roles", response_model=List[RoleSchema])
def get_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = False,
) -> List[RoleSchema]:
    """Get all dynamic roles."""
    _check_admin_permission(current_user)

    query = db.query(DynamicRole)
    if not include_inactive:
        query = query.filter(DynamicRole.is_active.is_(True))

    roles = query.order_by(DynamicRole.created_at.desc()).all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleSchema)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleSchema:
    """Get a specific role by ID."""
    _check_admin_permission(current_user)
    return _get_role_or_404(db, role_id)


@router.post("/roles", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleSchema:
    """Create a new dynamic role."""
    _check_admin_permission(current_user)

    # Check if role name already exists
    existing_role = (
        db.query(DynamicRole).filter(DynamicRole.name == role_data.name).first()
    )
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.name}' already exists.",
        )

    # Validate permission IDs
    permissions = []
    if role_data.permission_ids:
        permissions = _validate_permission_ids(db, role_data.permission_ids)

    # Create new role
    new_role = DynamicRole(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        color=role_data.color,
        dashboard_view=role_data.dashboard_view,
        is_system=False,  # User-created roles are not system roles
        is_active=True,
    )

    # Add permissions
    new_role.permissions = permissions

    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return new_role


@router.put("/roles/{role_id}", response_model=RoleSchema)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleSchema:
    """Update an existing role."""
    _check_admin_permission(current_user)

    role = _get_role_or_404(db, role_id)

    # Check if trying to modify a system role
    if role.is_system and role_data.permission_ids is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions of system roles.",
        )

    # Update fields
    if role_data.display_name is not None:
        role.display_name = role_data.display_name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.color is not None:
        role.color = role_data.color
    if role_data.dashboard_view is not None:
        role.dashboard_view = role_data.dashboard_view
    if role_data.is_active is not None:
        role.is_active = role_data.is_active

    # Update permissions if provided
    if role_data.permission_ids is not None:
        permissions = _validate_permission_ids(db, role_data.permission_ids)
        role.permissions = permissions

    db.commit()
    db.refresh(role)

    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a role (soft delete by marking as inactive)."""
    _check_admin_permission(current_user)

    role = _get_role_or_404(db, role_id)

    # Check if it's a system role
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles.",
        )

    # Check if any users are assigned to this role
    from server.db.models import User

    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {user_count} assigned users. "
            f"Reassign users first or mark role as inactive.",
        )

    # Soft delete by marking as inactive
    role.is_active = False
    db.commit()


# ============================================================================
# Permission Endpoints
# ============================================================================


@router.get("/permissions", response_model=List[PermissionSchema])
def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = False,
) -> List[PermissionSchema]:
    """Get all permissions."""
    _check_admin_permission(current_user)

    query = db.query(Permission)
    if not include_inactive:
        query = query.filter(Permission.is_active.is_(True))

    permissions = query.order_by(Permission.category, Permission.code).all()
    return permissions


@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PermissionSchema:
    """Get a specific permission by ID."""
    _check_admin_permission(current_user)
    return _get_permission_or_404(db, permission_id)


@router.post(
    "/permissions", response_model=PermissionSchema, status_code=status.HTTP_201_CREATED
)
def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PermissionSchema:
    """Create a new permission."""
    _check_admin_permission(current_user)

    # Check if permission code already exists
    existing = (
        db.query(Permission).filter(Permission.code == permission_data.code).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission with code '{permission_data.code}' already exists.",
        )

    # Create new permission
    new_permission = Permission(
        code=permission_data.code,
        name=permission_data.name,
        category=permission_data.category,
        description=permission_data.description,
        is_system=False,  # User-created permissions are not system permissions
        is_active=True,
    )

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    return new_permission


@router.put("/permissions/{permission_id}", response_model=PermissionSchema)
def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PermissionSchema:
    """Update an existing permission."""
    _check_admin_permission(current_user)

    permission = _get_permission_or_404(db, permission_id)

    # Check if trying to modify a system permission
    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system permissions.",
        )

    # Update fields
    if permission_data.name is not None:
        permission.name = permission_data.name
    if permission_data.category is not None:
        permission.category = permission_data.category
    if permission_data.description is not None:
        permission.description = permission_data.description
    if permission_data.is_active is not None:
        permission.is_active = permission_data.is_active

    db.commit()
    db.refresh(permission)

    return permission


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a permission (soft delete by marking as inactive)."""
    _check_admin_permission(current_user)

    permission = _get_permission_or_404(db, permission_id)

    # Check if it's a system permission
    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system permissions.",
        )

    # Check if any roles have this permission
    role_count = (
        db.query(RolePermission)
        .filter(RolePermission.permission_id == permission_id)
        .count()
    )
    if role_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete permission used by {role_count} roles. "
            f"Remove from roles first or mark permission as inactive.",
        )

    # Soft delete by marking as inactive
    permission.is_active = False
    db.commit()


# ============================================================================
# Role-Permission Management Endpoints
# ============================================================================


@router.put("/role-permissions", response_model=RoleSchema)
def update_role_permissions(
    update_data: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoleSchema:
    """Update permissions for a specific role."""
    _check_admin_permission(current_user)

    role = _get_role_or_404(db, update_data.role_id)

    # Check if trying to modify a system role
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions of system roles.",
        )

    # Validate permission IDs
    permissions = _validate_permission_ids(db, update_data.permission_ids)

    # Update role permissions
    role.permissions = permissions

    db.commit()
    db.refresh(role)

    return role


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionSchema])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PermissionSchema]:
    """Get all permissions for a specific role."""
    _check_admin_permission(current_user)

    role = _get_role_or_404(db, role_id)
    return role.permissions


# ============================================================================
# Catalogue Endpoints (Public)
# ============================================================================


@router.get("/catalogue/roles", response_model=List[dict])
def get_role_catalogue(
    db: Session = Depends(get_db),
    include_inactive: bool = False,
) -> List[dict]:
    """Get role catalogue for dropdowns (no admin auth required)."""
    query = db.query(DynamicRole)
    if not include_inactive:
        query = query.filter(DynamicRole.is_active.is_(True))

    roles = query.order_by(DynamicRole.display_name).all()

    return [
        {
            "value": role.id,
            "label": role.display_name,
            "color": role.color,
            "dashboard_view": role.dashboard_view,
            "is_system": role.is_system,
        }
        for role in roles
    ]


@router.get("/catalogue/permissions", response_model=List[dict])
def get_permission_catalogue(
    db: Session = Depends(get_db),
    include_inactive: bool = False,
) -> List[dict]:
    """Get permission catalogue grouped by category (no admin auth required)."""
    query = db.query(Permission)
    if not include_inactive:
        query = query.filter(Permission.is_active.is_(True))

    permissions = query.order_by(Permission.category, Permission.name).all()

    # Group by category
    categories = {}
    for perm in permissions:
        if perm.category not in categories:
            categories[perm.category] = []
        categories[perm.category].append(
            {
                "id": perm.id,
                "code": perm.code,
                "name": perm.name,
                "description": perm.description,
            }
        )

    # Convert to list format
    result = []
    for category, perms in categories.items():
        result.append(
            {
                "category": category.title(),
                "permissions": perms,
            }
        )

    return result
