<template>
  <a-config-provider>
    <div id="app">
      <!-- 路由视图 -->
      <router-view />
      
      <!-- 全局消息提示容器 -->
      <a-message-provider />
      <a-notification-provider />
      <a-modal-provider />

      <!-- OTA 更新通知（仅桌面端有效） -->
      <UpdateNotifier />
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import UpdateNotifier from '@/components/UpdateNotifier.vue'
</script>

<style>
#app {
  min-height: 100vh;
  width: 100%;
}
</style>