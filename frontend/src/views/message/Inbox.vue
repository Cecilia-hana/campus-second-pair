<template>
  <el-card>
    <h3>站内消息</h3>
    <el-table :data="list" stripe>
      <el-table-column prop="senderId" label="发件人" width="120">
        <template #default="{row}">
          <span v-if="row.senderId === 0">系统</span>
          <span v-else>用户 {{ row.senderId }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" />
      <el-table-column prop="createdAt" label="时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{row}">
          <el-button v-if="row.senderId !== 0" size="small" @click="$router.push('/messages/' + row.senderId)">回复</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api'

const list = ref([])
onMounted(async () => { list.value = (await api.get('/api/message/inbox')).data })
</script>
