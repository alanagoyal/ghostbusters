'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo, useRef, useEffect, useState } from 'react'

interface TimeSlot {
  time: Date
  label: string
  count: number
}

interface ActivityTimelineProps {
  detections: Array<{ timestamp: string }>
}

// Constants
const SLOT_DURATION_MS = 15 * 60 * 1000 // 15 minutes in milliseconds
const SLOT_WIDTH_PX = 32 // Width per slot in pixels
const Y_AXIS_WIDTH_PX = 32 // Width of y-axis label column

export function ActivityTimeline({ detections }: ActivityTimelineProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)
  const [isReady, setIsReady] = useState(false)

  // Measure container width
  useEffect(() => {
    const updateWidth = () => {
      if (scrollContainerRef.current) {
        const width = scrollContainerRef.current.offsetWidth
        setContainerWidth(width)
        if (!isReady && width > 0) {
          setIsReady(true)
        }
      }
    }

    // Use requestAnimationFrame to ensure measurement after layout
    const rafId = requestAnimationFrame(() => {
      updateWidth()
    })

    window.addEventListener('resize', updateWidth)
    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('resize', updateWidth)
    }
  }, [isReady])

  const timeSlotData = useMemo(() => {
    const now = Date.now()

    // Calculate how many slots fit in the visible area (default to showing 2 hours worth)
    const visibleSlots = containerWidth > 0
      ? Math.floor((containerWidth - Y_AXIS_WIDTH_PX) / SLOT_WIDTH_PX)
      : 8

    // Determine start and end time based on detections
    let startTime: Date
    let endTime: Date

    if (detections.length === 0) {
      // If no detections, default to current time
      endTime = new Date(now)
      endTime.setMinutes(Math.ceil(endTime.getMinutes() / 15) * 15, 0, 0)
      startTime = new Date(endTime.getTime() - visibleSlots * SLOT_DURATION_MS)
    } else {
      // Use earliest and latest detection times
      const timestamps = detections.map(d => new Date(d.timestamp).getTime())
      const earliest = Math.min(...timestamps)
      const latest = Math.max(...timestamps)

      // Set end time to latest detection, rounded up to nearest 15 minutes
      endTime = new Date(latest)
      endTime.setMinutes(Math.ceil(endTime.getMinutes() / 15) * 15, 0, 0)

      // Set start time to earliest detection, rounded down to nearest 15 minutes
      startTime = new Date(earliest)
      startTime.setMinutes(Math.floor(startTime.getMinutes() / 15) * 15, 0, 0)

      // Ensure we have enough slots to fill the visible area
      const minStartTime = new Date(endTime.getTime() - visibleSlots * SLOT_DURATION_MS)
      if (startTime > minStartTime) {
        startTime = minStartTime
      }
    }

    // Create time slots from start to end
    const slots: TimeSlot[] = []
    let currentTime = new Date(startTime)

    while (currentTime <= endTime) {
      const hours = currentTime.getHours()
      const minutes = currentTime.getMinutes()
      const label = `${hours % 12 || 12}:${minutes.toString().padStart(2, '0')}`

      slots.push({
        time: new Date(currentTime),
        label,
        count: 0
      })

      currentTime = new Date(currentTime.getTime() + SLOT_DURATION_MS)
    }

    // Count detections in each slot
    detections.forEach(detection => {
      const detectionTime = new Date(detection.timestamp)

      // Find which slot this detection belongs to
      for (let i = 0; i < slots.length; i++) {
        const slotStart = slots[i].time
        const slotEnd = new Date(slotStart.getTime() + SLOT_DURATION_MS)

        if (detectionTime >= slotStart && detectionTime < slotEnd) {
          slots[i].count++
          break
        }
      }
    })

    return slots
  }, [detections, containerWidth])

  // Auto-scroll to the end (most recent) when ready
  useEffect(() => {
    if (isReady && scrollContainerRef.current) {
      // Use requestAnimationFrame to ensure scroll happens after render
      requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth
        }
      })
    }
  }, [isReady])

  const maxCount = timeSlotData.length > 0 ? Math.max(...timeSlotData.map(h => h.count), 1) : 1
  const peakSlot = timeSlotData.length > 0 ? timeSlotData.reduce((max, h) => h.count > max.count ? h : max, timeSlotData[0]) : null

  // Calculate a nice y-axis scale based on the max count
  const calculateYAxisScale = (max: number): number => {
    if (max <= 5) return 5
    if (max <= 10) return 10
    if (max <= 20) return 20
    if (max <= 50) return 50
    if (max <= 100) return 100
    // For larger values, round up to nearest 50
    return Math.ceil(max / 50) * 50
  }

  const yAxisMax = calculateYAxisScale(maxCount)
  const yAxisTicks = Array.from({ length: 6 }, (_, i) => Math.round((yAxisMax / 5) * i))

  return (
    <Card className="col-span-2">
        <CardHeader>
        <div className="space-y-1">
          <CardTitle>Activity Timeline</CardTitle>
          <CardDescription>
            {peakSlot ? (
              <>Peak activity around {peakSlot.label} {peakSlot.time.getHours() >= 12 ? 'PM' : 'AM'} with {peakSlot.count} visitor{peakSlot.count !== 1 ? 's' : ''}</>
            ) : (
              <>No activity data available</>
            )}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative h-56 flex">
          {/* Sticky Y-axis labels */}
          <div className="relative" style={{ width: `${Y_AXIS_WIDTH_PX}px`, flexShrink: 0 }}>
            {isReady && (
              <div className="absolute top-0 left-0 right-0" style={{ bottom: '2rem' }}>
                {yAxisTicks.map((tick) => (
                  <div
                    key={tick}
                    className="absolute"
                    style={{
                      bottom: `${(tick / yAxisMax) * 100}%`,
                      left: 0,
                      right: 0,
                    }}
                  >
                    <div className="absolute left-0 -top-2 text-xs text-muted-foreground">
                      {tick}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Scrollable chart area */}
          <div className="flex-1 relative overflow-x-auto overflow-y-hidden" ref={scrollContainerRef}>
            {isReady && (
              <div className="relative h-full" style={{ width: `${Math.max(timeSlotData.length * SLOT_WIDTH_PX, containerWidth || 800)}px`, height: '100%' }}>
                {/* Y-axis grid lines */}
                <div className="absolute top-0 left-0 right-0" style={{ bottom: '2rem' }}>
                {yAxisTicks.map((tick) => {
                  const position = (tick / yAxisMax) * 100;
                  // For the top line (100%), offset it by 1px so it's visible
                  const bottomStyle = position === 100
                    ? `calc(${position}% - 1px)`
                    : `${position}%`;

                  return (
                    <div
                      key={tick}
                      className="absolute w-full border-t border-border/50"
                      style={{
                        bottom: bottomStyle,
                      }}
                    />
                  );
                })}
              </div>

              {/* Bars - aligned with grid */}
              <div className="absolute top-0 left-0 right-0 flex gap-1" style={{ bottom: '2rem' }}>
                {timeSlotData.map((slot, index) => {
                  const heightPercent = (slot.count / yAxisMax) * 100;
                  const ampm = slot.time.getHours() >= 12 ? 'PM' : 'AM';

                  return (
                    <div key={index} className="flex-1 flex justify-center relative min-w-0">
                      <div
                        className={`w-full rounded-t-sm transition-all duration-300 absolute bottom-0 ${
                          slot.count > 0 ? 'hover:bg-primary/80 bg-primary' : 'bg-muted'
                        }`}
                        style={{
                          height: `${Math.max(heightPercent, 0)}%`,
                          minHeight: slot.count > 0 ? '4px' : '0',
                        }}
                        title={`${slot.count} visitor${slot.count !== 1 ? 's' : ''} around ${slot.label} ${ampm}`}
                      />
                    </div>
                  )
                })}
              </div>

              {/* X-axis labels */}
              <div className="absolute bottom-0 left-0 right-0 flex">
                {timeSlotData.map((slot, index) => {
                  const showLabel = index % 2 === 0; // Show every 2nd label (every 30 minutes)

                  return (
                    <div key={index} className="flex-1 text-center min-w-0">
                      {showLabel && (
                        <div className="text-[10px] text-muted-foreground whitespace-nowrap">
                          {slot.label}
                          <div className="text-[8px] text-muted-foreground/50">
                            {slot.time.getHours() < 12 ? 'AM' : 'PM'}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
