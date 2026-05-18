<template>
  <el-card style="max-width: 720px; margin: 0 auto;">
    <h3>发布二手物品</h3>
    <el-form :model="form" label-width="80px">
      <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.categoryId" placeholder="选择分类">
          <el-option v-for="(name, id) in cats" :key="id" :value="Number(id)" :label="name" />
        </el-select>
      </el-form-item>
      <el-form-item label="价格">
        <el-input-number v-model="form.price" :min="0" :precision="2" :step="1" />
      </el-form-item>
      <el-form-item label="库存">
        <el-input-number v-model="form.stock" :min="1" :max="999" />
      </el-form-item>
      <el-form-item label="封面图">
        <el-upload :show-file-list="false" :before-upload="beforeUpload" :http-request="upload" accept="image/*">
          <el-button>选择图片(<=5MB)</el-button>
        </el-upload>
        <img v-if="form.coverUrl" :src="form.coverUrl" class="preview" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="4" />
      </el-form-item>
      <el-button type="primary" :loading="loading" @click="submit">发布</el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const cats = ref({})
const loading = ref(false)
const form = reactive({ title: '', categoryId: null, price: 0, stock: 1, coverUrl: '', description: '' })

onMounted(async () => {
  const r = await api.get('/api/item/categories')
  cats.value = r.data
})

function beforeUpload(file) {
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('图片不得超过 5MB'); return false }
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) {
    ElMessage.error('仅支持 jpeg/png/webp'); return false
  }
}

async function upload(opt) {
  const fd = new FormData(); fd.append('file', opt.file)
  const r = await api.post('/api/item/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' }})
  form.coverUrl = r.data.url
  ElMessage.success('上传成功')
}

async function submit() {
  if (!form.coverUrl) return ElMessage.warning('请先上传封面图')
  loading.value = true
  try {
    await api.post('/api/item/create', form)
    ElMessage.success('发布成功')
    router.push('/')
  } finally { loading.value = false }
}
</script>

<style scoped>
.preview { display: block; max-width: 220px; margin-top: 12px; border: 1px solid #eee; border-radius: 4px; }
</style>
