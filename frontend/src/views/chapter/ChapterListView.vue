<template>
  <div class="page-container">
    <div class="page-header">
      <h2>章节列表</h2>
    </div>

    <el-row :gutter="20">
      <el-col
        v-for="chapter in chapters"
        :key="chapter.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
        class="chapter-col"
      >
        <el-card shadow="never" class="chapter-card" @click="router.push(`/chapters/${chapter.id}/learn`)">
          <div class="chapter-order">{{ chapter.order }}</div>
          <h3 class="chapter-title">{{ chapter.title }}</h3>
          <p class="chapter-desc">{{ chapter.description || '暂无描述' }}</p>
          <div class="chapter-footer">
            <el-tag size="small" :type="statusType(chapter.status)">
              {{ statusLabel(chapter.status) }}
            </el-tag>
            <span class="chapter-docs">
              <el-icon><Document /></el-icon>
              {{ chapter.document_count }} 个文档
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && chapters.length === 0" description="暂无章节" />

    <!-- 加载骨架 -->
    <el-row :gutter="20" v-if="loading">
      <el-col v-for="i in 8" :key="i" :xs="24" :sm="12" :md="8" :lg="6" class="chapter-col">
        <el-card shadow="never">
          <div class="skeleton-loading" style="height: 160px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import { getChapters, type Chapter } from '@/api/chapter'

const router = useRouter()
const chapters = ref<Chapter[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getChapters({ status: 'published' })
    chapters.value = res.data
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})

function statusType(status: string): 'success' | 'warning' | 'info' {
  switch (status) {
    case 'published': return 'success'
    case 'draft': return 'warning'
    case 'archived': return 'info'
    default: return 'info'
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'published': return '已发布'
    case 'draft': return '草稿'
    case 'archived': return '已归档'
    default: return status
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chapter-col {
  margin-bottom: 20px;
}

.chapter-card {
  cursor: pointer;
  transition: transform $transition-fast, box-shadow $transition-fast;
  height: 100%;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-md;
  }
}

.chapter-order {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, $primary-color, $primary-dark);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
}

.chapter-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
}

.chapter-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: $text-secondary;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chapter-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chapter-docs {
  font-size: 12px;
  color: $text-secondary;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
