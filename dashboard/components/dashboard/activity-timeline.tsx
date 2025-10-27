'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo } from 'react'

interface TimeSlot {
  hour: number
  count: number
}

interface ActivityTimelineProps {
  detections: Array<{ timestamp: string }>
}

export function ActivityTimeline({ detections }: ActivityTimelineProps) {
  const hourlyData = useMemo(() => {
    const hours = new Array(24).fill(0)

    detections.forEach(detection => {
      const hour = new Date(detection.timestamp).getHours()
      hours[hour]++
    })

    return hours.map((count, hour) => ({ hour, count }))
  }, [detections])

  const maxCount = Math.max(...hourlyData.map(h => h.count), 1)
  const peakHour = hourlyData.reduce((max, h) => h.count > max.count ? h : max, hourlyData[0])

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Activity by Hour</CardTitle>
        <CardDescription>
          Peak activity at {peakHour.hour % 12 || 12}:00 {peakHour.hour >= 12 ? 'PM' : 'AM'} with {peakHour.count} visitors
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between h-48 gap-1">
          {hourlyData.map(({ hour, count }) => {
            const height = maxCount > 0 ? (count / maxCount) * 100 : 0
            const isEveningHour = hour >= 17 && hour <= 21

            return (
              <div key={hour} className="flex-1 flex flex-col items-center gap-1 group">
                <div className="flex-1 w-full flex items-end justify-center">
                  <div
                    className={`w-full rounded-t transition-all duration-300 ${
                      isEveningHour ? 'bg-primary' : 'bg-primary/40'
                    } ${count > 0 ? 'hover:opacity-80' : ''}`}
                    style={{ height: `${height}%` }}
                  />
                </div>
                {hour % 3 === 0 && (
                  <span className="text-[10px] text-muted-foreground">
                    {hour % 12 || 12}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
