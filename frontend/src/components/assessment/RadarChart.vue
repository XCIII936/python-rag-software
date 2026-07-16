<template>
  <div ref="chartRef" class="radar-chart" :style="{ height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

interface DimensionScore {
  name: string
  score: number
  weight?: number
}

const props = withDefaults(
  defineProps<{
    dimensions: DimensionScore[]
    height?: string
    seriesName?: string
  }>(),
  {
    height: '320px',
    seriesName: '维度得分',
  }
)

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function renderChart() {
  if (!chartRef.value) return
  if (!props.dimensions || props.dimensions.length === 0) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const indicators = props.dimensions.map((d) => ({
    name: d.name,
    max: 100,
  }))
  const values = props.dimensions.map((d) => d.score)

  chartInstance.setOption({
    tooltip: { trigger: 'item' },
    radar: {
      indicator: indicators,
      radius: '65%',
      splitNumber: 4,
      axisName: {
        color: '#606266',
        fontSize: 13,
      },
      splitArea: {
        areaStyle: {
          color: ['#fafafa', '#f0f2f5'],
        },
      },
    },
    series: [
      {
        name: props.seriesName,
        type: 'radar',
        data: [
          {
            value: values,
            name: props.seriesName,
            areaStyle: { color: 'rgba(64, 158, 255, 0.25)' },
            lineStyle: { color: '#409EFF', width: 2 },
            itemStyle: { color: '#409EFF' },
          },
        ],
      },
    ],
  })
}

function resizeChart() {
  chartInstance?.resize()
}

onMounted(() => {
  nextTick(renderChart)
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chartInstance?.dispose()
  chartInstance = null
})

watch(
  () => props.dimensions,
  () => nextTick(renderChart),
  { deep: true }
)
</script>

<style scoped>
.radar-chart {
  width: 100%;
}
</style>
