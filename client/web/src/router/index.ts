/**
 * 路由配置 - 权限点驱动版本
 *
 * 路由守卫不再硬编码角色名。每条需要特殊权限的路由在 meta 中
 * 声明所需的权限点字符串（如 "view:shadow_audit"），守卫统一
 * 调用 permissionStore.can(permission) 进行校验。
 *
 * 新增角色或调整权限：只需修改后端 permissions.py，前端零改动。
 */

import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { auth } from '@/utils/auth'
import { usePermissionStore } from '@/stores/permission'
import { useWorkflowStore } from '@/stores/workflow'
import { rbacApi } from '@/api/rbac'

import MainLayout from '@/layouts/MainLayout.vue'

const LoginPage            = () => import('@/views/LoginPage.vue')
const DashboardPage        = () => import('@/views/DashboardPage.vue')
const RealTimePatrolPage   = () => import('@/views/RealTimePatrolPage.vue')
const ViolationReviewPage  = () => import('@/views/ViolationReviewPage.vue')
const SOPPage              = () => import('@/views/SOPPage.vue')
const SettingsPage         = () => import('@/views/SettingsPage.vue')
const NotFoundPage         = () => import('@/views/NotFoundPage.vue')
const ShadowAuditDashboard = () => import('@/views/supervisor/ShadowAuditDashboard.vue')

// ---------------------------------------------------------------------------
// Route table
// meta.permission  — if set, user must hold this permission point
// meta.requiresAuth — if true, user must be logged in
// ---------------------------------------------------------------------------
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { title: '登录', requiresAuth: false, hideLayout: true },
  },
  {
    path: '/desktop/violation-popup',
    name: 'ViolationPopupWindow',
    component: () => import('@/views/ViolationPopupStandalone.vue'),
    meta: {
      title: '违规处置',
      requiresAuth: true,
      permission: 'view:realtime',
      hideLayout: true,
    },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: DashboardPage,
        meta: {
          title: '工作概览',
          icon: 'icon-dashboard',
          menu: true,
          requiresAuth: true,
          // 移除权限限制：所有登录用户都能访问 Dashboard
          // 具体显示内容由 DashboardPage 组件根据角色决定
        },
      },
      {
        path: 'risk-audit',
        name: 'RiskAudit',
        redirect: '/risk-audit/realtime',
        meta: { title: '实时监看', icon: 'icon-shield', menu: true, requiresAuth: true },
        children: [
          {
            path: 'realtime',
            name: 'RealTimePatrol',
            component: RealTimePatrolPage,
            meta: { title: '直播监测', requiresAuth: true, permission: 'view:realtime' },
          },
          {
            path: 'violation-review',
            name: 'ViolationReview',
            component: ViolationReviewPage,
            meta: { title: '内容审核', requiresAuth: true, permission: 'view:violations' },
          },
        ],
      },
      {
        path: 'sop',
        name: 'SOP',
        redirect: '/sop/standards',
        meta: { title: '审核标准', icon: 'icon-book', menu: true, requiresAuth: true },
        children: [
          {
            path: 'standards',
            name: 'SOPStandards',
            component: SOPPage,
            meta: { title: '红线标准', requiresAuth: true, permission: 'view:sop' },
          },
          {
            path: 'rules',
            name: 'SOPRules',
            component: () => import('@/views/SOPRulesPage.vue'),
            meta: { title: '业务规则', requiresAuth: true, permission: 'view:sop' },
          },
        ],
      },
      {
        path: 'supervisor/shadow-audit',
        name: 'ShadowAuditDashboard',
        component: ShadowAuditDashboard,
        meta: {
          title: '管理大屏',
          icon: 'icon-eye',
          menu: true,
          requiresAuth: true,
          permission: 'view:shadow_audit',   // only manager in matrix
        },
      },
      {
        path: 'dashboard/hr',
        name: 'Settings',
        component: SettingsPage,
        meta: {
          title: '人事权限',
          icon: 'icon-team',
          menu: true,
          requiresAuth: true,
          permission: 'view:settings',
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundPage,
    meta: { title: '页面未找到', hideLayout: true },
  },
]

// file:// protocol (PyQt6 WebEngine) requires hash history;
// HTTP server mode works with either, so we use hash universally.
const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: (_to, _from, savedPosition) => savedPosition || { top: 0 },
})

// ---------------------------------------------------------------------------
// Navigation guard — permission-point driven, role-agnostic
// ---------------------------------------------------------------------------
router.beforeEach(async (to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 徽鉴 HuiInsight`
  }

  // -- 离开直播监测时：强制同步工作流进度到后端，确保概览数据最新 --------
  if (from.name === 'RealTimePatrol' && to.name !== 'RealTimePatrol') {
    const workflowStore = useWorkflowStore()
    if (workflowStore.isWorking && workflowStore.todayTaskId) {
      try {
        await rbacApi.updateTaskProgress(workflowStore.todayTaskId, {
          reviewed_count:  workflowStore.reviewedCount,
          violation_count: workflowStore.violationCount,
          work_duration:   workflowStore.totalSeconds,
          is_completed:    false,
        })
      } catch { /* 静默，不阻塞导航 */ }
    }
  }

  const token      = auth.getToken()
  const user       = auth.getUserInfo()
  const isLoggedIn = !!(token && user)

  // -- Auth check ----------------------------------------------------------
  if (to.meta.requiresAuth && !isLoggedIn) {
    if (to.path !== '/login') {
      Message.error('请先登录系统')
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    next()
    return
  }

  // -- Permission check ----------------------------------------------------
  if (to.meta.permission && isLoggedIn) {
    const permissionStore = usePermissionStore()
    if (permissionStore.hydrated && !permissionStore.can(to.meta.permission as string)) {
      Message.error('您没有访问该页面的权限')
      next({ name: 'Dashboard' })
      return
    }
    // If store not yet hydrated (first load), let the page through;
    // the component itself can do a secondary guard via can() in template.
  }

  // -- Redirect logged-in users away from login ----------------------------
  if (to.name === 'Login' && isLoggedIn) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
