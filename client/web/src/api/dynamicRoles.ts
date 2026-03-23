// -*- coding: utf-8 -*-
/**
 * Dynamic roles and permissions API client.
 * 
 * Provides methods for managing dynamic roles and permissions.
 * 
 * Author : AHDUNYI
 * Version: 9.1.0
 */

import api from '@/api'

// ============================================================================
// Types
// ============================================================================

export interface Role {
  id: number
  name: string
  display_name: string
  description?: string
  color: string
  dashboard_view: string
  is_system: boolean
  is_active: boolean
  created_at: string
  updated_at?: string
  permissions: Permission[]
  user_count?: number
  permission_count?: number
}

export interface Permission {
  id: number
  code: string
  name: string
  category: string
  description?: string
  is_system: boolean
  is_active: boolean
  created_at: string
}

export interface RoleCreate {
  name: string
  display_name: string
  description?: string
  color: string
  dashboard_view: string
  permission_ids?: number[]
}

export interface RoleUpdate {
  display_name?: string
  description?: string
  color?: string
  dashboard_view?: string
  is_active?: boolean
  permission_ids?: number[]
}

export interface PermissionCreate {
  code: string
  name: string
  category: string
  description?: string
}

export interface PermissionUpdate {
  name?: string
  category?: string
  description?: string
  is_active?: boolean
}

export interface RolePermissionUpdate {
  role_id: number
  permission_ids: number[]
}

export interface RoleCatalogueItem {
  value: number
  label: string
  color: string
  dashboard_view: string
  is_system: boolean
}

export interface PermissionCategory {
  category: string
  permissions: Array<{
    id: number
    code: string
    name: string
    description?: string
  }>
}

// ============================================================================
// API Methods
// ============================================================================

/**
 * Get all dynamic roles.
 * 
 * @param includeInactive - Whether to include inactive roles
 * @returns List of roles
 */
export const getDynamicRoles = (includeInactive: boolean = false) => {
  return api.get('/dynamic-roles/roles', {
    params: { include_inactive: includeInactive }
  })
}

/**
 * Get a specific role by ID.
 * 
 * @param roleId - Role ID
 * @returns Role details
 */
export const getRole = (roleId: number) => {
  return api.get(`/dynamic-roles/roles/${roleId}`)
}

/**
 * Create a new role.
 * 
 * @param data - Role data
 * @returns Created role
 */
export const createRole = (data: RoleCreate) => {
  return api.post('/dynamic-roles/roles', data)
}

/**
 * Update an existing role.
 * 
 * @param roleId - Role ID
 * @param data - Update data
 * @returns Updated role
 */
export const updateRole = (roleId: number, data: RoleUpdate) => {
  return api.put(`/dynamic-roles/roles/${roleId}`, data)
}

/**
 * Delete a role (soft delete by marking as inactive).
 * 
 * @param roleId - Role ID
 */
export const deleteRole = (roleId: number) => {
  return api.delete(`/dynamic-roles/roles/${roleId}`)
}

/**
 * Get all permissions.
 * 
 * @param includeInactive - Whether to include inactive permissions
 * @returns List of permissions
 */
export const getPermissions = (includeInactive: boolean = false) => {
  return api.get('/dynamic-roles/permissions', {
    params: { include_inactive: includeInactive }
  })
}

/**
 * Get a specific permission by ID.
 * 
 * @param permissionId - Permission ID
 * @returns Permission details
 */
export const getPermission = (permissionId: number) => {
  return api.get(`/dynamic-roles/permissions/${permissionId}`)
}

/**
 * Create a new permission.
 * 
 * @param data - Permission data
 * @returns Created permission
 */
export const createPermission = (data: PermissionCreate) => {
  return api.post('/dynamic-roles/permissions', data)
}

/**
 * Update an existing permission.
 * 
 * @param permissionId - Permission ID
 * @param data - Update data
 * @returns Updated permission
 */
export const updatePermission = (permissionId: number, data: PermissionUpdate) => {
  return api.put(`/dynamic-roles/permissions/${permissionId}`, data)
}

/**
 * Delete a permission (soft delete by marking as inactive).
 * 
 * @param permissionId - Permission ID
 */
export const deletePermission = (permissionId: number) => {
  return api.delete(`/dynamic-roles/permissions/${permissionId}`)
}

/**
 * Update permissions for a specific role.
 * 
 * @param roleId - Role ID
 * @param permissionIds - List of permission IDs
 * @returns Updated role
 */
export const updateRolePermissions = (roleId: number, permissionIds: number[]) => {
  return api.put('/dynamic-roles/role-permissions', {
    role_id: roleId,
    permission_ids: permissionIds
  })
}

/**
 * Get all permissions for a specific role.
 * 
 * @param roleId - Role ID
 * @returns List of permissions
 */
export const getRolePermissions = (roleId: number) => {
  return api.get(`/dynamic-roles/roles/${roleId}/permissions`)
}

/**
 * Get role catalogue for dropdowns.
 * 
 * @param includeInactive - Whether to include inactive roles
 * @returns Role catalogue
 */
export const getRoleCatalogue = (includeInactive: boolean = false) => {
  return api.get('/dynamic-roles/catalogue/roles', {
    params: { include_inactive: includeInactive }
  })
}

/**
 * Get permission catalogue grouped by category.
 * 
 * @param includeInactive - Whether to include inactive permissions
 * @returns Permission catalogue
 */
export const getPermissionCatalogue = (includeInactive: boolean = false) => {
  return api.get('/dynamic-roles/catalogue/permissions', {
    params: { include_inactive: includeInactive }
  })
}