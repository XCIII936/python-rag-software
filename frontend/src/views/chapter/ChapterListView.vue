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
          <div class="chapter-order">{{ chapter.order_index + 1 }}</div>
          <h3 class="chapter-title">{{ chapter.title }}</h3>
          <p class="chapter-desc">{{ chapter.description || '暂无描述' }}</p>
          <div class="chapter-footer">
            <el-tag v-if="chapter.is_active" size="small" type="success">已发布</el-tag>
            <el-tag v-else size="small" type="info">已归档</el-tag>
            <div class="chapter-progress">
              <component :is="progressStatus(chapter.id).icon" :color="progressStatus(chapter.id).color" :size="16" />
              <span :style="{ color: progressStatus(chapter.id).color, fontSize: '12px', marginLeft: '4px' }">
                {{ progressStatus(chapter.id).label }}
              </span>
              <span v-if="progressMap[chapter.id]?.best_score !== null && progressMap[chapter.id]?.best_score !== undefined"
                    style="margin-left: 8px; font-size: 12px; color: #909399;">
                {{ Math.round(progressMap[chapter.id].best_score!) }}分
              </span>
            </div>
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
import { Document, SuccessFilled, Clock, CircleClose } from '@element-plus/icons-vue'
import { getChapters, getProgress, type Chapter } from '@/api/chapter'

const router = useRouter()
const chapters = ref<Chapter[]>([])
const loading = ref(true)
const progressMap = ref<Record<number, { status: string; best_score: number | null }>>({})

onMounted(async () => {
  try {
    const [ch, prog] = await Promise.all([
      getChapters(),
      getProgress().catch(() => []),
    ])
    chapters.value = ch
    // Build progress map keyed by chapter id
    const map: Record<number, { status: string; best_score: number | null }> = {}
    for (const p of prog as any[]) {
      map[p.chapter_id] = { status: p.status, best_score: p.best_score }
    }
    progressMap.value = map
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})

function progressStatus(chapterId: number): { icon: any; label: string; color: string } {
  const p = progressMap.value[chapterId]
  if (!p) return { icon: CircleClose, label: '待学习', color: '#C0C4CC' }
  switch (p.status) {
    case 'completed': return { icon: SuccessFilled, label: '已完成', color: '#67C23A' }
    case 'pending': return { icon: Clock, label: '进行中', color: '#E6A23C' }
    default: return { icon: CircleClose, label: '待学习', color: '#C0C4CC' }
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

.chapter-progress {
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.chapter-docs {
  font-size: 12px;
  color: $text-secondary;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
