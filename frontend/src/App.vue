<template>
  <el-container class="app-shell">
    <el-header class="topbar">
      <div class="brand" @click="$router.push('/')">校园二手 · CampusSecond</div>
      <el-menu mode="horizontal" :router="true" :default-active="$route.path" class="nav">
        <el-menu-item index="/">商品市集</el-menu-item>
        <el-menu-item index="/publish" v-if="auth.user">发布</el-menu-item>
        <el-menu-item index="/orders/buy" v-if="auth.user">我买的</el-menu-item>
        <el-menu-item index="/orders/sell" v-if="auth.user">我卖的</el-menu-item>
        <el-menu-item index="/messages" v-if="auth.user">
          消息
          <el-badge :value="unread" :hidden="!unread" class="badge"/>
        </el-menu-item>
      </el-menu>
      <div class="right">
        <template v-if="auth.user">
          <span>{{ auth.user.nickname }}</span>
          <el-button link @click="logout">退出</el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="$router.push('/login')">登录 / 注册</el-button>
        </template>
      </div>
    </el-header>
    <el-main><router-view /></el-main>
  </el-container>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useAuthStore } from './store/auth'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from './api'
import { connectWS, closeWS } from './utils/ws'

const auth = useAuthStore()
const router = useRouter()
const unread = ref(0)

async function refreshUnread() {
  if (!auth.user) { unread.value = 0; return }
  try {
    const r = await api.get('/api/message/unread')
    unread.value = r.data.count || 0
  } catch {}
}

function setupWS() {
  if (!auth.user) return
  connectWS(auth.user.userId, (msg) => {
    if (msg.type === 'message') {
      ElMessage.success('收到新消息')
      refreshUnread()
    }
  })
}

onMounted(() => {
  if (auth.user) { refreshUnread(); setupWS() }
})

watch(() => auth.user, (u) => {
  if (u) { refreshUnread(); setupWS() } else { closeWS(); unread.value = 0 }
})

function logout() {
  auth.logout(); closeWS(); router.push('/')
}
</script>

<style>
.app-shell { min-height: 100vh; }
.topbar { display: flex; align-items: center; gap: 24px; background: #fff; border-bottom: 1px solid #eee; }
.brand { font-weight: 600; font-size: 18px; cursor: pointer; }
.nav { flex: 1; border-bottom: none; }
.right { display: flex; align-items: center; gap: 12px; }
.badge { margin-left: 6px; }
</style>
