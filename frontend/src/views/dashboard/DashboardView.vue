<template>
  <div class="page-container">
    <div class="page-header">
      <h2>仪表盘</h2>
      <span class="welcome-text">欢迎回来，{{ authStore.username }}</span>
    </div>

    <!-- 加载骨架 -->
    <template v-if="loading">
      <el-row :gutter="20">
        <el-col v-for="i in 4" :key="i" :span="6">
          <el-card shadow="never">
            <div class="stat-skeleton">
              <div class="skeleton-loading stat-label-skeleton"></div>
              <div class="skeleton-loading stat-value-skeleton"></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 统计卡片 -->
    <template v-else>
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">学生总数</div>
                <div class="stat-value">{{ stats?.total_students ?? 0 }}</div>
              </div>
              <div class="stat-icon stat-icon-students">
                <el-icon :size="32"><User /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">章节数量</div>
                <div class="stat-value">{{ stats?.total_chapters ?? 0 }}</div>
              </div>
              <div class="stat-icon stat-icon-chapters">
                <el-icon :size="32"><FolderOpened /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">文档数量</div>
                <div class="stat-value">{{ stats?.total_documents ?? 0 }}</div>
              </div>
              <div class="stat-icon stat-icon-documents">
                <el-icon :size="32"><Document /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-content">
              <div class="stat-info">
                <div class="stat-label">测评次数</div>
                <div class="stat-value">{{ stats?.total_assessments ?? 0 }}</div>
              </div>
              <div class="stat-icon stat-icon-assessments">
                <el-icon :size="32"><List /></el-icon>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 最近动态 -->
    <el-card shadow="never" class="activity-card">
      <template #header>
        <div class="card-header">
          <span>最近动态</span>
        </div>
      </template>

      <template v-if="loading">
        <div v-for="i in 5" :key="i" class="activity-skeleton-item">
          <div class="skeleton-loading activity-line-short"></div>
          <div class="skeleton-loading activity-line-long"></div>
        </div>
      </template>

      <template v-else-if="!stats?.recent_activity?.length">
        <el-empty description="暂无动态" :image-size="80" />
      </template>

      <template v-else>
        <div class="activity-timeline">
          <div
            v-for="item in stats.recent_activity"
            :key="item.id"
            class="activity-item"
          >
            <div class="activity-dot"></div>
            <div class="activity-body">
              <div class="activity-header">
                <span class="activity-user">{{ item.username }}</span>
                <span class="activity-action">{{ item.action }}</span>
                <el-tag size="small" type="info">{{ item.module }}</el-tag>
              </div>
              <div class="activity-detail">{{ item.detail }}</div>
              <div class="activity-time">{{ item.created_at }}</div>
            </div>
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { User, FolderOpened, Document, List } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getDashboardStats, type DashboardStats } from '@/api/system'

const authStore = useAuthStore()
const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await getDashboardStats()
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.welcome-text {
  font-size: $font-size-base;
  color: $text-secondary;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  transition: transform $transition-fast, box-shadow $transition-fast;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-md;
  }

  .stat-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .stat-info {
    flex: 1;
  }

  .stat-label {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: $text-primary;
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-icon-students {
    background-color: rgba(64, 158, 255, 0.1);
    color: #409EFF;
  }

  .stat-icon-chapters {
    background-color: rgba(103, 194, 58, 0.1);
    color: #67C23A;
  }

  .stat-icon-documents {
    background-color: rgba(230, 162, 60, 0.1);
    color: #E6A23C;
  }

  .stat-icon-assessments {
    background-color: rgba(144, 147, 153, 0.1);
    color: #909399;
  }
}

// ========== 骨架屏 ==========
.stat-skeleton {
  padding: 8px 0;
}

.stat-label-skeleton {
  width: 60%;
  height: 14px;
  margin-bottom: 12px;
}

.stat-value-skeleton {
  width: 40%;
  height: 28px;
}

.activity-skeleton-item {
  padding: 12px 0;
  border-bottom: 1px solid $border-lighter;

  .activity-line-short {
    width: 30%;
    height: 14px;
    margin-bottom: 8px;
  }

  .activity-line-long {
    width: 70%;
    height: 14px;
  }
}

// ========== 动态 ==========
.activity-card {
  margin-top: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.activity-timeline {
  padding: 0;
}

.activity-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid $border-lighter;

  &:last-child {
    border-bottom: none;
  }
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: $primary-color;
  margin-top: 6px;
  flex-shrink: 0;
}

.activity-body {
  flex: 1;
  min-width: 0;
}

.activity-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.activity-user {
  font-weight: 600;
  color: $text-primary;
}

.activity-action {
  color: $text-regular;
}

.activity-detail {
  color: $text-secondary;
  font-size: $font-size-sm;
  margin-bottom: 4px;
}

.activity-time {
  color: $text-placeholder;
  font-size: $font-size-xs;
}
</style>
