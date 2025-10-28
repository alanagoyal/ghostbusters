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

    const result = hours.map((count, hour) => ({ hour, count }));
    return result;
  }, [detections])

  const maxCount = Math.max(...hourlyData.map(h => h.count), 1)
  const peakHour = hourlyData.reduce((max, h) => h.count > max.count ? h : max, hourlyData[0])

  return (
    <Card className="col-span-2">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="space-y-1">
            <CardTitle>Activity by Hour</CardTitle>
            <CardDescription>
              Peak activity at {peakHour.hour % 12 || 12}:00 {peakHour.hour >= 12 ? 'PM' : 'AM'} with {peakHour.count} visitors
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground sm:pt-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary/40 flex-shrink-0"></div>
              <span>Day</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary flex-shrink-0"></div>
              <span>Evening (5-9 PM)</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Y-axis grid lines */}
          <div className="absolute top-0 left-0 right-0 bottom-8 -z-10">
            {[0, 1, 2, 3, 4, 5].map((tick) => (
              <div 
                key={tick}
                className="absolute w-full border-b border-border/50"
                style={{
                  bottom: `${(tick / 5) * 100}%`,
                  height: '1px'
                }}
              >
                <div className="absolute left-0 sm:-left-8 -top-2 text-xs text-muted-foreground">
                  {tick === 0 ? '' : tick}
                </div>
              </div>
            ))}
          </div>
          
          {/* Bars */}
          <div className="flex items-end justify-between h-48 gap-0.5 pl-6 sm:pl-8">
            {hourlyData.map(({ hour, count }) => {
              const height = count > 0 
                ? Math.max(5, (count / maxCount) * 100) 
                : 0;
              const isEveningHour = hour >= 17 && hour <= 21;
              const hourLabel = hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`;
              const isMajorTick = hour % 3 === 0;

              return (
                <div key={hour} className="flex-1 flex flex-col items-center h-full group relative">
                  {/* Bar */}
                  <div className="flex-1 w-full flex items-end justify-center">
                    <div
                      className={`w-3/4 rounded-t-sm transition-all duration-300 ${
                        isEveningHour ? 'bg-primary' : 'bg-primary/40'
                      } ${count > 0 ? 'hover:bg-primary/80' : 'bg-muted'}`}
                      style={{
                        height: `${height}%`,
                        minHeight: count > 0 ? '4px' : '0',
                      }}
                      title={`${count} visitor${count !== 1 ? 's' : ''} at ${hourLabel}`}
                    />
                  </div>
                  
                  {/* X-axis labels */}
                  <div className={`w-full text-center mt-1 ${isMajorTick ? '' : 'h-4'}`}>
                    {isMajorTick && (
                      <div className="text-[10px] text-muted-foreground">
                        {hour % 12 || 12}
                        <div className="text-[8px] text-muted-foreground/50">
                          {hour < 12 ? 'AM' : 'PM'}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Hover count */}
                  {count > 0 && (
                    <div className="absolute -top-6 text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-background/90 px-1.5 py-0.5 rounded-md border shadow-sm">
                      {count} visitor{count !== 1 ? 's' : ''} at {hourLabel}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
