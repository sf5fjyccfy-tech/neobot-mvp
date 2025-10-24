'use client'

import { useRouter } from 'next/navigation'

interface Alert {
  type: 'warning' | 'danger' | 'info'
  title: string
  message: string
  action: string
  action_url: string
  icon: string
}

interface AlertBannerProps {
  alerts: Alert[]
}

export default function AlertBanner({ alerts }: AlertBannerProps) {
  const router = useRouter()

  if (alerts.length === 0) return null

  const getAlertStyles = (type: string) => {
    switch (type) {
      case 'danger':
        return {
          bg: 'bg-red-50 border-red-200',
          text: 'text-red-900',
          button: 'bg-red-600 hover:bg-red-700 text-white'
        }
      case 'warning':
        return {
          bg: 'bg-yellow-50 border-yellow-200',
          text: 'text-yellow-900',
          button: 'bg-yellow-600 hover:bg-yellow-700 text-white'
        }
      case 'info':
        return {
          bg: 'bg-blue-50 border-blue-200',
          text: 'text-blue-900',
          button: 'bg-blue-600 hover:bg-blue-700 text-white'
        }
      default:
        return {
          bg: 'bg-gray-50 border-gray-200',
          text: 'text-gray-900',
          button: 'bg-gray-600 hover:bg-gray-700 text-white'
        }
    }
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => {
        const styles = getAlertStyles(alert.type)
        
        return (
          <div
            key={index}
            className={`${styles.bg} border rounded-lg p-4 flex items-start justify-between`}
          >
            <div className="flex items-start space-x-3 flex-1">
              <span className="text-2xl">{alert.icon}</span>
              <div className="flex-1">
                <h3 className={`font-semibold ${styles.text} mb-1`}>
                  {alert.title}
                </h3>
                <p className={`text-sm ${styles.text} opacity-90`}>
                  {alert.message}
                </p>
              </div>
            </div>
            
            <button
              onClick={() => router.push(alert.action_url)}
              className={`${styles.button} px-4 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ml-4`}
            >
              {alert.action}
            </button>
          </div>
        )
      })}
    </div>
  )
}
