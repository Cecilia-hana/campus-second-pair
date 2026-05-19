<template>
  <el-card>
    <h3>与 用户{{ otherId }} 的对话</h3>
    <div class="msg-list" ref="boxRef">
      <div v-for="m in list" :key="m.id" :class="['bubble', m.senderId === me ? 'mine' : 'other']">
        <div class="content">{{ m.content }}</div>
        <div class="time">{{ m.createdAt }}</div>
      </div>
    </div>
    <div class="input">
      <el-input v-model="text" type="textarea" :rows="2" placeholder="输入消息后回车发送" @keyup.enter.exact.prevent="send" />
      <el-button type="primary" @click="send">发送</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'
import { useAuthStore } from '../../store/auth'

const route = useRoute()
const auth = useAuthStore()
const otherId = computed(() => Number(route.params.other))
const me = auth.user?.userId
const list = ref([])
const text = ref('')
const boxRef = ref(null)

async function load() {
  list.value = (await api.get('/api/message/conversation/' + otherId.value)).data
  await nextTick()
  if (boxRef.value) boxRef.value.scrollTop = boxRef.value.scrollHeight
}

async function send() {
  if (!text.value.trim()) return
  await api.post('/api/message/send', { receiverId: otherId.value, content: text.value })
  text.value = ''
  load()
}

onMounted(load)
</script>

<style scoped>
.msg-list { height: 50vh; overflow-y: auto; padding: 12px; background: #f7f8fa; border-radius: 4px; }
.bubble { margin: 8px 0; max-width: 60%; padding: 8px 12px; border-radius: 8px; clear: both; }
.bubble.mine  { background: #b3d8ff; float: right; }
.bubble.other { background: #fff;     float: left;  border: 1px solid #eee; }
.bubble .time { font-size: 11px; color: #999; margin-top: 4px; }
.input { display: flex; gap: 12px; margin-top: 12px; }
</style>
