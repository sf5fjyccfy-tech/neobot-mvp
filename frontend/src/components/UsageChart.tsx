'use client'

import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface UsageChartProps {
  data: number[]
  labels: string[]
}

export default function UsageChart({ data, labels }: UsageChartProps) {
  const chartData = {
    labels,
    datasets: [{
      label: 'Messages',
      data,
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.3
    }]
  }

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: false }
    },
    scales: {
      y: { beginAtZero: true }
    }
  }

  return <Line data={chartData} options={options} />
}
