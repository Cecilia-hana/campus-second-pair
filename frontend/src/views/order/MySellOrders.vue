<template>
  <el-card>
    <h3>我卖的订单</h3>
    <el-table :data="list" stripe>
      <el-table-column prop="orderNo" label="订单号" width="200" />
      <el-table-column label="商品">
        <template #default="{row}">
          <div v-for="i in row.items" :key="i.id">{{ i.itemTitle }} × {{ i.quantity }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="totalAmount" label="金额" width="100" />
      <el-table-column prop="statusText" label="状态" width="100" />
      <el-table-column prop="createdAt" label="时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{row}">
          <el-button v-if="row.status === 1" size="small" type="primary" @click="ship(row)">发货</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const list = ref([])
async function load() { list.value = (await api.get('/api/order/my/sell')).data }
async function ship(row) {
  await api.post('/api/order/ship/' + row.id)
  ElMessage.success('已发货'); load()
}
onMounted(load)
</script>
