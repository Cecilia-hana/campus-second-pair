<template>
  <el-card class="login-card">
    <el-tabs v-model="tab">
      <el-tab-pane name="login" label="登录">
        <el-form :model="loginForm" label-width="70px">
          <el-form-item label="用户名"><el-input v-model="loginForm.username" /></el-form-item>
          <el-form-item label="密码"><el-input type="password" v-model="loginForm.password" show-password /></el-form-item>
          <el-button type="primary" @click="onLogin" :loading="loading" style="width: 100%">登录</el-button>
        </el-form>
      </el-tab-pane>
      <el-tab-pane name="reg" label="注册">
        <el-form :model="regForm" label-width="70px">
          <el-form-item label="用户名"><el-input v-model="regForm.username" /></el-form-item>
          <el-form-item label="昵称"><el-input v-model="regForm.nickname" /></el-form-item>
          <el-form-item label="密码"><el-input type="password" v-model="regForm.password" show-password /></el-form-item>
          <el-button type="primary" @click="onReg" :loading="loading" style="width: 100%">注册</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>
    <p class="hint">测试账号:stu001 / 123456 (买家),stu002 / 123456 (卖家)</p>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api from '../../api'
import { useAuthStore } from '../../store/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const tab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', nickname: '', password: '' })
const auth = useAuthStore()
const router = useRouter()

async function onLogin() {
  if (!loginForm.username || !loginForm.password) return ElMessage.warning('请填写完整')
  loading.value = true
  try {
    const r = await api.post('/api/user/login', loginForm)
    auth.setUser(r.data, r.data.token)
    ElMessage.success('登录成功')
    router.push('/')
  } finally { loading.value = false }
}

async function onReg() {
  if (!regForm.username || !regForm.password) return ElMessage.warning('请填写完整')
  loading.value = true
  try {
    await api.post('/api/user/register', regForm)
    ElMessage.success('注册成功,请登录')
    tab.value = 'login'
    loginForm.username = regForm.username
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-card { max-width: 380px; margin: 60px auto; }
.hint { color: #999; font-size: 12px; margin-top: 16px; text-align: center; }
</style>
