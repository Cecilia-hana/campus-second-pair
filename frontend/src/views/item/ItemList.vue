<template>
  <div>
    <div class="filter">
      <el-input v-model="q.keyword" placeholder="搜索商品" clearable style="width: 240px" @keyup.enter="reload" />
      <el-select v-model="q.categoryId" placeholder="分类" clearable style="width: 160px" @change="reload">
        <el-option v-for="(name, id) in cats" :key="id" :value="Number(id)" :label="name" />
      </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="it in list" :key="it.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="item-card" shadow="hover" @click="$router.push('/item/' + it.id)">
          <img :src="it.coverUrl" class="cover" referrerpolicy="no-referrer" />
          <h4 class="title">{{ it.title }}</h4>
          <div class="row">
            <span class="price">¥{{ it.price }}</span>
            <span class="seller">{{ it.sellerNickname }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-pagination class="pager"
      background layout="prev, pager, next, total"
      :total="total" :page-size="q.size" v-model:current-page="q.page"
      @current-change="reload" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api'

const q = reactive({ keyword: '', categoryId: null, page: 1, size: 12 })
const list = ref([])
const total = ref(0)
const cats = ref({})

async function reload() {
  const r = await api.post('/api/item/list', q)
  list.value = r.data.records
  total.value = r.data.total
}

onMounted(async () => {
  const c = await api.get('/api/item/categories')
  cats.value = c.data
  await reload()
})
</script>

<style scoped>
.filter { display: flex; gap: 12px; margin-bottom: 16px; }
.item-card { margin-bottom: 16px; cursor: pointer; }
.cover { width: 100%; height: 180px; object-fit: cover; border-radius: 4px; background: #f5f5f5; }
.title { margin: 8px 0 4px; font-size: 15px; }
.row { display: flex; justify-content: space-between; align-items: center; }
.price { color: #f56c6c; font-weight: bold; font-size: 18px; }
.seller { color: #999; font-size: 12px; }
.pager { margin-top: 24px; text-align: center; display: flex; justify-content: center; }
</style>
