'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemo, useRef, useEffect, useState } from 'react'

interface TimeSlot {
  time: Date
  label: string
  count: number
  detectionTimestamps: number[]
}

interface ActivityTimelineProps {
  detections: Array<{ timestamp: string }>
}

// Constants
const SLOT_DURATION_MS = 15 * 60 * 1000 // 15 minutes in milliseconds
const SLOT_WIDTH_PX = 32 // Width per slot in pixels
const Y_AXIS_WIDTH_PX = 32 // Width of y-axis label column
const PULSE_DURATION_MS = 3000 // Duration of one pulse
const PULSE_COUNT = 3 // Number of times to pulse
const TOTAL_PULSE_DURATION_MS = PULSE_DURATION_MS * PULSE_COUNT // Total animation duration (9 seconds)
const UPDATE_INTERVAL_MS = 1000 // Update current time every second

export function ActivityTimeline({ detections }: ActivityTimelineProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)
  const [currentTime, setCurrentTime] = useState<number | null>(null)
  const [mountTime, setMountTime] = useState<number | null>(null)
  const [isReady, setIsReady] = useState(false)

  // Set current time on client only and update every second
  useEffect(() => {
    const now = Date.now()
    setCurrentTime(now)
    setMountTime(now)
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, UPDATE_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

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

    // End time is always current time, rounded up to nearest 15 minutes
    const endTime = new Date(now)
    endTime.setMinutes(Math.ceil(endTime.getMinutes() / 15) * 15, 0, 0)

    // Determine start time
    let startTime: Date
    if (detections.length === 0) {
      // If no detections, go back enough to fill the visible area
      startTime = new Date(endTime.getTime() - visibleSlots * SLOT_DURATION_MS)
    } else {
      // Use earliest detection time
      const timestamps = detections.map(d => new Date(d.timestamp).getTime())
      const earliest = Math.min(...timestamps)
      startTime = new Date(earliest)

      // Round start time down to nearest 15 minutes
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
        count: 0,
        detectionTimestamps: []
      })

      currentTime = new Date(currentTime.getTime() + SLOT_DURATION_MS)
    }

    // Count detections in each slot and track timestamps
    detections.forEach(detection => {
      const detectionTime = new Date(detection.timestamp)

      // Find which slot this detection belongs to
      for (let i = 0; i < slots.length; i++) {
        const slotStart = slots[i].time
        const slotEnd = new Date(slotStart.getTime() + SLOT_DURATION_MS)

        if (detectionTime >= slotStart && detectionTime < slotEnd) {
          slots[i].count++
          slots[i].detectionTimestamps.push(detectionTime.getTime())
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
    <>
      <style>{`
        @keyframes slow-pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        .slow-pulse {
          animation: slow-pulse ${PULSE_DURATION_MS}ms cubic-bezier(0.4, 0, 0.6, 1) ${PULSE_COUNT};
        }
      `}</style>
      <Card className="col-span-2">
        <CardHeader>
        <div className="space-y-1">
          <CardTitle>Activity Timeline</CardTitle>
          <CardDescription>
            {peakSlot ? (
              <>Peak activity at {peakSlot.label} {peakSlot.time.getHours() >= 12 ? 'PM' : 'AM'} with {peakSlot.count} visitor{peakSlot.count !== 1 ? 's' : ''}</>
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

                  // Check if this slot has any detections from the last pulse duration
                  const hasRecentDetection = currentTime
                    ? slot.detectionTimestamps.some(ts => ts >= currentTime - TOTAL_PULSE_DURATION_MS)
                    : false;

                  // Check if this is the current time slot and we're within the pulse duration of mount
                  const slotStart = slot.time.getTime();
                  const slotEnd = slotStart + SLOT_DURATION_MS;
                  const isCurrentSlot = currentTime && currentTime >= slotStart && currentTime < slotEnd;
                  const isInitialAnimation = mountTime && currentTime && (currentTime - mountTime) < TOTAL_PULSE_DURATION_MS;
                  const shouldPulse = hasRecentDetection || (isCurrentSlot && isInitialAnimation);

                  return (
                    <div key={index} className="flex-1 flex justify-center relative min-w-0">
                      <div
                        className={`w-full rounded-t-sm transition-all duration-300 absolute bottom-0 ${
                          slot.count > 0 ? 'hover:bg-primary/80' : 'bg-muted'
                        } ${shouldPulse ? 'slow-pulse bg-primary' : 'bg-primary'}`}
                        style={{
                          height: `${Math.max(heightPercent, 0)}%`,
                          minHeight: slot.count > 0 ? '4px' : '0',
                        }}
                        title={`${slot.count} visitor${slot.count !== 1 ? 's' : ''} at ${slot.label} ${ampm}`}
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
    </>
  )
}
