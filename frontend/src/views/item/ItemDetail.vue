<template>
  <el-card v-if="item">
    <el-row :gutter="24">
      <el-col :md="10">
        <img :src="item.coverUrl" class="cover" />
      </el-col>
      <el-col :md="14">
        <h2>{{ item.title }}</h2>
        <p class="price">¥{{ item.price }}</p>
        <p>分类:<el-tag>{{ item.categoryName }}</el-tag></p>
        <p>库存:{{ item.stock }}</p>
        <p>卖家:{{ item.sellerNickname }}</p>
        <pre class="desc">{{ item.description }}</pre>

        <div v-if="auth.user && auth.user.userId !== item.sellerId" class="actions">
          <el-input-number v-model="qty" :min="1" :max="item.stock" />
          <el-button type="primary" @click="buy">立即购买</el-button>
          <el-button @click="chat">私信卖家</el-button>
        </div>
        <p v-else-if="auth.user && auth.user.userId === item.sellerId" class="own">这是你发布的商品</p>
        <p v-else>请先 <router-link to="/login">登录</router-link> 后购买</p>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import { useAuthStore } from '../../store/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const item = ref(null)
const qty = ref(1)

async function load() {
  const r = await api.get('/api/item/detail/' + route.params.id)
  item.value = r.data
}

async function buy() {
  try {
    await ElMessageBox.confirm(`确认下单 ${qty.value} 件,共 ¥${(qty.value * item.value.price).toFixed(2)}?`, '提示')
  } catch { return }
  const r = await api.post('/api/order/create', { itemId: item.value.id, quantity: qty.value })
  ElMessage.success('下单成功 ' + r.data.orderNo)
  router.push('/orders/buy')
}

function chat() { router.push('/messages/' + item.value.sellerId) }

onMounted(load)
</script>

<style scoped>
.cover { width: 100%; max-height: 420px; object-fit: cover; border-radius: 4px; }
.price { color: #f56c6c; font-size: 28px; font-weight: bold; margin: 12px 0; }
.desc { white-space: pre-wrap; background: #fafafa; padding: 12px; border-radius: 4px; }
.actions { margin-top: 24px; display: flex; gap: 12px; align-items: center; }
.own { color: #909399; margin-top: 16px; }
</style>
