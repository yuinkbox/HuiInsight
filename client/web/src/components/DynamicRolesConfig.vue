<template>
  <a-modal
    v-model:visible="visible"
    title="🎯 动态角色与权限配置"
    width="1200px"
    :footer="false"
    :mask-closable="false"
    @cancel="handleCancel"
  >
    <div class="dynamic-roles-config">
      <!-- 顶部操作栏 -->
      <div class="config-header">
        <a-space>
          <a-button type="primary" @click="handleAddRole">
            <template #icon>
              <icon-plus />
            </template>
            新增角色
          </a-button>
          <a-button type="outline" @click="handleAddPermission">
            <template #icon>
              <icon-plus />
            </template>
            新增权限
          </a-button>
          <a-button type="text" @click="refreshData">
            <template #icon>
              <icon-refresh />
            </template>
            刷新
          </a-button>
        </a-space>
        
        <div class="header-stats">
          <a-tag color="blue">角色: {{ roles.length }}</a-tag>
          <a-tag color="green">权限: {{ permissions.length }}</a-tag>
          <a-tag color="orange">系统角色: {{ systemRolesCount }}</a-tag>
        </div>
      </div>
      
      <!-- 主内容区域 -->
      <div class="config-content">
        <!-- 左侧：角色列表 -->
        <div class="roles-panel">
          <div class="panel-header">
            <h3>📋 角色列表</h3>
            <a-input-search
              v-model="roleSearch"
              placeholder="搜索角色..."
              size="small"
              style="width: 200px"
            />
          </div>
          
          <div class="roles-list">
            <a-list
              :data="filteredRoles"
              :bordered="false"
              :split="false"
              size="small"
              :loading="loadingRoles"
            >
              <template #item="{ item }">
                <div
                  class="role-item"
                  :class="{ active: selectedRoleId === item.id, 'system-role': item.is_system }"
                  @click="selectRole(item)"
                >
                  <div class="role-item-header">
                    <div class="role-color" :style="{ backgroundColor: item.color }"></div>
                    <div class="role-info">
                      <div class="role-name">
                        <strong>{{ item.display_name }}</strong>
                        <a-tag v-if="item.is_system" size="small" color="orange">系统</a-tag>
                        <a-tag v-if="!item.is_active" size="small" color="red">禁用</a-tag>
                      </div>
                      <div class="role-code">{{ item.name }}</div>
                    </div>
                    <div class="role-actions">
                      <a-dropdown :trigger="['click']" position="br">
                        <a-button type="text" size="mini">
                          <icon-more />
                        </a-button>
                        <template #content>
                          <a-doption @click="handleEditRole(item)">
                            <template #icon>
                              <icon-edit />
                            </template>
                            编辑
                          </a-doption>
                          <a-doption
                            v-if="!item.is_system"
                            @click="handleToggleRoleStatus(item)"
                            :disabled="item.user_count > 0"
                          >
                            <template #icon>
                              <icon-poweroff />
                            </template>
                            {{ item.is_active ? '禁用' : '启用' }}
                          </a-doption>
                          <a-doption
                            v-if="!item.is_system && item.user_count === 0"
                            @click="handleDeleteRole(item)"
                            class="danger-option"
                          >
                            <template #icon>
                              <icon-delete />
                            </template>
                            删除
                          </a-doption>
                        </template>
                      </a-dropdown>
                    </div>
                  </div>
                  
                  <div class="role-stats">
                    <div class="stat-item">
                      <icon-user />
                      <span>{{ item.user_count || 0 }} 用户</span>
                    </div>
                    <div class="stat-item">
                      <icon-key />
                      <span>{{ item.permission_count || 0 }} 权限</span>
                    </div>
                  </div>
                  
                  <div class="role-description" v-if="item.description">
                    {{ item.description }}
                  </div>
                </div>
              </template>
              
              <template #empty>
                <a-empty description="暂无角色数据">
                  <template #image>
                    <icon-user-group />
                  </template>
                </a-empty>
              </template>
            </a-list>
          </div>
        </div>
        
        <!-- 右侧：权限配置 -->
        <div class="permissions-panel">
          <div class="panel-header">
            <h3 v-if="selectedRole">
              🔐 {{ selectedRole.display_name }} - 权限配置
            </h3>
            <h3 v-else>🔐 请选择一个角色</h3>
            
            <div v-if="selectedRole" class="role-actions">
              <a-button
                type="primary"
                size="small"
                @click="handleSavePermissions"
                :loading="savingPermissions"
                :disabled="selectedRole.is_system"
              >
                <template #icon>
                  <icon-save />
                </template>
                保存权限
              </a-button>
              <a-button
                type="outline"
                size="small"
                @click="handleSelectAll"
                :disabled="selectedRole.is_system"
              >
                全选
              </a-button>
              <a-button
                type="outline"
                size="small"
                @click="handleClearAll"
                :disabled="selectedRole.is_system"
              >
                清空
              </a-button>
            </div>
          </div>
          
          <div v-if="selectedRole" class="permissions-content">
            <!-- 权限分类 -->
            <div
              v-for="category in permissionCategories"
              :key="category.category"
              class="permission-category"
            >
              <div class="category-header">
                <h4>{{ category.category }}</h4>
                <a-checkbox
                  :model-value="isCategorySelected(category.category)"
                  :indeterminate="isCategoryIndeterminate(category.category)"
                  @change="(checked: boolean) => toggleCategory(category.category, checked)"
                  :disabled="selectedRole.is_system"
                >
                  全选
                </a-checkbox>
              </div>
              
              <div class="permission-items">
                <div
                  v-for="permission in category.permissions"
                  :key="permission.id"
                  class="permission-item"
                >
                  <a-checkbox
                    :model-value="isPermissionSelected(permission.id)"
                    @change="(checked: boolean) => togglePermission(permission.id, checked)"
                    :disabled="selectedRole.is_system || !permission.is_active"
                  >
                    <div class="permission-info">
                      <div class="permission-name">
                        {{ permission.name }}
                        <a-tag v-if="!permission.is_active" size="small" color="red">禁用</a-tag>
                        <a-tag v-if="permission.is_system" size="small" color="orange">系统</a-tag>
                      </div>
                      <div class="permission-code">{{ permission.code }}</div>
                      <div class="permission-description" v-if="permission.description">
                        {{ permission.description }}
                      </div>
                    </div>
                  </a-checkbox>
                </div>
              </div>
            </div>
            
            <div v-if="permissionCategories.length === 0" class="empty-permissions">
              <a-empty description="暂无权限数据">
                <template #image>
                  <icon-key />
                </template>
              </a-empty>
            </div>
          </div>
          
          <div v-else class="no-role-selected">
            <a-empty description="请从左侧选择一个角色进行权限配置">
              <template #image>
                <icon-user-group />
              </template>
            </a-empty>
          </div>
        </div>
      </div>
    </div>
  </a-modal>
  
  <!-- 角色编辑对话框 -->
  <a-modal
    v-model:visible="roleDialogVisible"
    :title="editingRole ? '编辑角色' : '新增角色'"
    width="500px"
    @ok="handleSaveRole"
    @cancel="handleCancelRoleDialog"
  >
    <a-form
      ref="roleFormRef"
      :model="roleForm"
      :rules="roleRules"
      layout="vertical"
    >
      <a-form-item label="角色标识" field="name" required>
        <a-input
          v-model="roleForm.name"
          placeholder="例如: team_leader, auditor"
          :disabled="editingRole?.is_system"
        />
        <template #extra>
          仅允许小写字母和下划线，用于系统内部识别
        </template>
      </a-form-item>
      
      <a-form-item label="显示名称" field="display_name" required>
        <a-input
          v-model="roleForm.display_name"
          placeholder="例如: 组长, 审核员"
        />
      </a-form-item>
      
      <a-form-item label="描述" field="description">
        <a-textarea
          v-model="roleForm.description"
          placeholder="角色描述..."
          :max-length="500"
          show-word-limit
        />
      </a-form-item>
      
      <a-form-item label="颜色" field="color" required>
        <a-color-picker
          v-model="roleForm.color"
          :show-preview="true"
          format="hex"
        />
      </a-form-item>
      
      <a-form-item label="仪表盘视图" field="dashboard_view" required>
        <a-select v-model="roleForm.dashboard_view">
          <a-option value="auditor">审核员视图</a-option>
          <a-option value="supervisor">主管视图</a-option>
          <a-option value="manager">经理视图</a-option>
          <a-option value="admin">管理员视图</a-option>
        </a-select>
      </a-form-item>
      
      <a-form-item label="状态" field="is_active" v-if="editingRole">
        <a-switch v-model="roleForm.is_active">
          <template #checked>启用</template>
          <template #unchecked>禁用</template>
        </a-switch>
      </a-form-item>
    </a-form>
  </a-modal>
  
  <!-- 权限编辑对话框 -->
  <a-modal
    v-model:visible="permissionDialogVisible"
    :title="editingPermission ? '编辑权限' : '新增权限'"
    width="500px"
    @ok="handleSavePermission"
    @cancel="handleCancelPermissionDialog"
  >
    <a-form
      ref="permissionFormRef"
      :model="permissionForm"
      :rules="permissionRules"
      layout="vertical"
    >
      <a-form-item label="权限标识" field="code" required>
        <a-input
          v-model="permissionForm.code"
          placeholder="例如: action:update_role, view:dashboard"
          :disabled="editingPermission?.is_system"
        />
        <template #extra>
          格式: category:action，仅允许小写字母、下划线和冒号
        </template>
      </a-form-item>
      
      <a-form-item label="权限名称" field="name" required>
        <a-input
          v-model="permissionForm.name"
          placeholder="例如: 更新角色权限, 查看仪表盘"
        />
      </a-form-item>
      
      <a-form-item label="分类" field="category" required>
        <a-input
          v-model="permissionForm.category"
          placeholder="例如: action, view, manage"
        />
      </a-form-item>
      
      <a-form-item label="描述" field="description">
        <a-textarea
          v-model="permissionForm.description"
          placeholder="权限描述..."
          :max-length="500"
          show-word-limit
        />
      </a-form-item>
      
      <a-form-item label="状态" field="is_active" v-if="editingPermission">
        <a-switch v-model="permissionForm.is_active">
          <template #checked>启用</template>
          <template #unchecked>禁用</template>
        </a-switch>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import type { FormInstance } from '@arco-design/web-vue'
import {
  getDynamicRoles,
  getPermissions,
  updateRolePermissions,
  createRole,
  updateRole,
  deleteRole,
  createPermission,
  updatePermission,
  getRoleCatalogue,
  getPermissionCatalogue
} from '@/api/dynamicRoles'

interface Role {
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

interface Permission {
  id: number
  code: string
  name: string
  category: string
  description?: string
  is_system: boolean
  is_active: boolean
  created_at: string
}

interface PermissionCategory {
  category: string
  permissions: Permission[]
}

// 模态框控制
const visible = ref(false)
const roleDialogVisible = ref(false)
const permissionDialogVisible = ref(false)

// 数据状态
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const selectedRoleId = ref<number | null>(null)
const selectedPermissions = ref<Set<number>>(new Set())

// 加载状态
const loadingRoles = ref(false)
const loadingPermissions = ref(false)
const savingPermissions = ref(false)

// 搜索
const roleSearch = ref('')

// 表单数据
const editingRole = ref<Role | null>(null)
const editingPermission = ref<Permission | null>(null)
const roleFormRef = ref<FormInstance>()
const permissionFormRef = ref<FormInstance>()

const roleForm = ref({
  name: '',
  display_name: '',
  description: '',
  color: '#1890ff',
  dashboard_view: 'auditor',
  is_active: true
})

const permissionForm = ref({
  code: '',
  name: '',
  category: 'general',
  description: '',
  is_active: true
})

// 表单验证规则
const roleRules = {
  name: [
    { required: true, message: '请输入角色标识' },
    { pattern: /^[a-z_]+$/, message: '仅允许小写字母和下划线' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称' }
  ],
  color: [
    { required: true, message: '请选择颜色' }
  ],
  dashboard_view: [
    { required: true, message: '请选择仪表盘视图' }
  ]
}

const permissionRules = {
  code: [
    { required: true, message: '请输入权限标识' },
    { pattern: /^[a-z_:]+$/, message: '仅允许小写字母、下划线和冒号' }
  ],
  name: [
    { required: true, message: '请输入权限名称' }
  ],
  category: [
    { required: true, message: '请输入分类' }
  ]
}

// 计算属性
const filteredRoles = computed(() => {
  if (!roleSearch.value) return roles.value
  const search = roleSearch.value.toLowerCase()
  return roles.value.filter(role =>
    role.name.toLowerCase().includes(search) ||
    role.display_name.toLowerCase().includes(search) ||
    role.description?.toLowerCase().includes(search)
  )
})

const selectedRole = computed(() => {
  return roles.value.find(role => role.id === selectedRoleId.value) || null
})

const permissionCategories = computed(() => {
  const categories: Record<string, Permission[]> = {}
  
  permissions.value.forEach(permission => {
    if (!categories[permission.category]) {
      categories[permission.category] = []
    }
    // TypeScript knows categories[permission.category] exists after the check above
    categories[permission.category]!.push(permission)
  })
  
  return Object.entries(categories).map(([category, permissions]) => ({
    category: category.charAt(0).toUpperCase() + category.slice(1),
    permissions
  }))
})

const systemRolesCount = computed(() => {
  return roles.value.filter(role => role.is_system).length
})

// 方法
const show = () => {
  visible.value = true
  loadData()
}

const hide = () => {
  visible.value = false
  resetState()
}

const handleCancel = () => {
  hide()
}

const loadData = async () => {
  await Promise.all([loadRoles(), loadPermissions()])
}

const loadRoles = async () => {
  try {
    loadingRoles.value = true
    const response = await getDynamicRoles()
    roles.value = response.data
  } catch (error) {
    Message.error('加载角色失败')
    console.error('Failed to load roles:', error)
  } finally {
    loadingRoles.value = false
  }
}

const loadPermissions = async () => {
  try {
    loadingPermissions.value = true
    const response = await getPermissions()
    permissions.value = response.data
  } catch (error) {
    Message.error('加载权限失败')
    console.error('Failed to load permissions:', error)
  } finally {
    loadingPermissions.value = false
  }
}

const refreshData = () => {
  loadData()
}

const selectRole = (role: Role) => {
  selectedRoleId.value = role.id
  selectedPermissions.value = new Set(role.permissions.map(p => p.id))
}

const isPermissionSelected = (permissionId: number) => {
  return selectedPermissions.value.has(permissionId)
}

const isCategorySelected = (category: string) => {
  const categoryPermissions = permissions.value.filter(p => 
    p.category === category.toLowerCase() && p.is_active
  )
  if (categoryPermissions.length === 0) return false
  return categoryPermissions.every(p => selectedPermissions.value.has(p.id))
}

const isCategoryIndeterminate = (category: string) => {
  const categoryPermissions = permissions.value.filter(p => 
    p.category === category.toLowerCase() && p.is_active
  )
  if (categoryPermissions.length === 0) return false
  
  const selectedCount = categoryPermissions.filter(p => 
    selectedPermissions.value.has(p.id)
  ).length
  
  return selectedCount > 0 && selectedCount < categoryPermissions.length
}

const togglePermission = (permissionId: number, checked: boolean) => {
  if (checked) {
    selectedPermissions.value.add(permissionId)
  } else {
    selectedPermissions.value.delete(permissionId)
  }
}

const toggleCategory = (category: string, checked: boolean) => {
  const categoryPermissions = permissions.value.filter(p => 
    p.category === category.toLowerCase() && p.is_active
  )
  
  categoryPermissions.forEach(permission => {
    if (checked) {
      selectedPermissions.value.add(permission.id)
    } else {
      selectedPermissions.value.delete(permission.id)
    }
  })
}

const handleSelectAll = () => {
  const activePermissions = permissions.value.filter(p => p.is_active)
  selectedPermissions.value = new Set(activePermissions.map(p => p.id))
}

const handleClearAll = () => {
  selectedPermissions.value.clear()
}

const handleSavePermissions = async () => {
  if (!selectedRole.value) return
  
  try {
    savingPermissions.value = true
    await updateRolePermissions(selectedRole.value.id, Array.from(selectedPermissions.value))
    
    // 更新本地角色数据
    const roleIndex = roles.value.findIndex(r => r.id === selectedRole.value!.id)
    if (roleIndex !== -1) {
      const updatedPermissions = permissions.value.filter(p => 
        selectedPermissions.value.has(p.id)
      )
      // TypeScript knows roles.value[roleIndex] exists because roleIndex !== -1
      const role = roles.value[roleIndex]!
      role.permissions = updatedPermissions
      role.permission_count = updatedPermissions.length
    }
    
    Message.success('权限保存成功')
  } catch (error) {
    Message.error('保存权限失败')
    console.error('Failed to save permissions:', error)
  } finally {
    savingPermissions.value = false
  }
}

const handleAddRole = () => {
  editingRole.value = null
  roleForm.value = {
    name: '',
    display_name: '',
    description: '',
    color: '#1890ff',
    dashboard_view: 'auditor',
    is_active: true
  }
  roleDialogVisible.value = true
}

const handleEditRole = (role: Role) => {
  editingRole.value = role
  roleForm.value = {
    name: role.name,
    display_name: role.display_name,
    description: role.description || '',
    color: role.color,
    dashboard_view: role.dashboard_view,
    is_active: role.is_active
  }
  roleDialogVisible.value = true
}

const handleSaveRole = async () => {
  const valid = await roleFormRef.value?.validate()
  if (!valid) return
  
  try {
    if (editingRole.value) {
      // 更新角色
      await updateRole(editingRole.value.id, roleForm.value)
      Message.success('角色更新成功')
    } else {
      // 创建角色
      await createRole(roleForm.value)
      Message.success('角色创建成功')
    }
    
    roleDialogVisible.value = false
    await loadRoles()
  } catch (error) {
    Message.error(editingRole.value ? '更新角色失败' : '创建角色失败')
    console.error('Failed to save role:', error)
  }
}

const handleToggleRoleStatus = async (role: Role) => {
  try {
    await updateRole(role.id, { is_active: !role.is_active })
    Message.success(`角色已${!role.is_active ? '启用' : '禁用'}`)
    await loadRoles()
  } catch (error) {
    Message.error('操作失败')
    console.error('Failed to toggle role status:', error)
  }
}

const handleDeleteRole = async (role: Role) => {
  try {
    await deleteRole(role.id)
    Message.success('角色删除成功')
    
    // 如果删除的是当前选中的角色，清空选择
    if (selectedRoleId.value === role.id) {
      selectedRoleId.value = null
      selectedPermissions.value.clear()
    }
    
    await loadRoles()
  } catch (error) {
    Message.error('删除角色失败')
    console.error('Failed to delete role:', error)
  }
}

const handleCancelRoleDialog = () => {
  roleDialogVisible.value = false
  roleFormRef.value?.resetFields()
}

const handleAddPermission = () => {
  editingPermission.value = null
  permissionForm.value = {
    code: '',
    name: '',
    category: 'general',
    description: '',
    is_active: true
  }
  permissionDialogVisible.value = true
}

const handleSavePermission = async () => {
  const valid = await permissionFormRef.value?.validate()
  if (!valid) return
  
  try {
    if (editingPermission.value) {
      // 更新权限
      await updatePermission(editingPermission.value.id, permissionForm.value)
      Message.success('权限更新成功')
    } else {
      // 创建权限
      await createPermission(permissionForm.value)
      Message.success('权限创建成功')
    }
    
    permissionDialogVisible.value = false
    await loadPermissions()
  } catch (error) {
    Message.error(editingPermission.value ? '更新权限失败' : '创建权限失败')
    console.error('Failed to save permission:', error)
  }
}

const handleCancelPermissionDialog = () => {
  permissionDialogVisible.value = false
  permissionFormRef.value?.resetFields()
}

const resetState = () => {
  selectedRoleId.value = null
  selectedPermissions.value.clear()
  roleSearch.value = ''
}

// 暴露方法给父组件
defineExpose({
  show,
  hide
})
</script>

<style scoped lang="less">
.dynamic-roles-config {
  display: flex;
  flex-direction: column;
  height: 70vh;
  
  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-border);
    
    .header-stats {
      display: flex;
      gap: 8px;
    }
  }
  
  .config-content {
    display: flex;
    flex: 1;
    gap: 16px;
    overflow: hidden;
    
    .roles-panel {
      flex: 0 0 350px;
      display: flex;
      flex-direction: column;
      border-right: 1px solid var(--color-border);
      padding-right: 16px;
      
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        
        h3 {
          margin: 0;
          font-size: 16px;
        }
      }
      
      .roles-list {
        flex: 1;
        overflow-y: auto;
        
        .role-item {
          padding: 12px;
          margin-bottom: 8px;
          border: 1px solid var(--color-border);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
          
          &:hover {
            border-color: var(--color-primary-light-3);
            background-color: var(--color-fill-2);
          }
          
          &.active {
            border-color: var(--color-primary);
            background-color: var(--color-primary-light-1);
          }
          
          &.system-role {
            border-left: 3px solid var(--color-orange);
          }
          
          .role-item-header {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            
            .role-color {
              width: 16px;
              height: 16px;
              border-radius: 4px;
              flex-shrink: 0;
              margin-top: 4px;
            }
            
            .role-info {
              flex: 1;
              
              .role-name {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 4px;
                
                strong {
                  font-size: 14px;
                }
              }
              
              .role-code {
                font-size: 12px;
                color: var(--color-text-3);
                font-family: monospace;
              }
            }
            
            .role-actions {
              flex-shrink: 0;
            }
          }
          
          .role-stats {
            display: flex;
            gap: 16px;
            margin-top: 8px;
            font-size: 12px;
            color: var(--color-text-3);
            
            .stat-item {
              display: flex;
              align-items: center;
              gap: 4px;
            }
          }
          
          .role-description {
            margin-top: 8px;
            font-size: 12px;
            color: var(--color-text-2);
            line-height: 1.4;
          }
        }
      }
    }
    
    .permissions-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        
        h3 {
          margin: 0;
          font-size: 16px;
        }
        
        .role-actions {
          display: flex;
          gap: 8px;
        }
      }
      
      .permissions-content {
        flex: 1;
        overflow-y: auto;
        
        .permission-category {
          margin-bottom: 24px;
          
          .category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--color-border);
            
            h4 {
              margin: 0;
              font-size: 14px;
              color: var(--color-text-1);
            }
          }
          
          .permission-items {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 12px;
            
            .permission-item {
              padding: 12px;
              border: 1px solid var(--color-border);
              border-radius: 6px;
              background-color: var(--color-fill-1);
              
              :deep(.arco-checkbox) {
                    width: 100%;
                    
                    .arco-checkbox-label {
                      width: 100%;
                    }
                  }
              
              .permission-info {
                .permission-name {
                  display: flex;
                  align-items: center;
                  gap: 8px;
                  margin-bottom: 4px;
                  font-weight: 500;
                }
                
                .permission-code {
                  font-size: 12px;
                  color: var(--color-text-3);
                  font-family: monospace;
                  margin-bottom: 4px;
                }
                
                .permission-description {
                  font-size: 12px;
                  color: var(--color-text-2);
                  line-height: 1.4;
                }
              }
            }
          }
        }
        
        .empty-permissions {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
        }
      }
      
      .no-role-selected {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
      }
    }
  }
}

.danger-option {
  :deep(.arco-dropdown-option) {
    color: var(--color-danger) !important;
    
    &:hover {
      background-color: var(--color-danger-light-1) !important;
    }
  }
}
</style>