"use client"

import { useEffect, useRef, useState } from "react"

interface AnimatedNumberProps {
  value: number
  decimals?: number
  duration?: number
  className?: string
  prefix?: string
  suffix?: string
  scramble?: boolean
}

export function AnimatedNumber({
  value,
  decimals = 0,
  duration = 800,
  className = "",
  prefix = "",
  suffix = "",
  scramble = true,
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(value)
  const [isAnimating, setIsAnimating] = useState(false)
  const prevValueRef = useRef(value)
  const frameRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    if (prevValueRef.current === value) return

    setIsAnimating(true)
    const startValue = prevValueRef.current
    const endValue = value
    const startTime = Date.now()
    const valueRange = endValue - startValue

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)

      if (scramble && progress < 0.6) {
        // Scramble phase - show random numbers for visual effect
        const scrambleIntensity = 1 - progress / 0.6
        const randomOffset = (Math.random() - 0.5) * Math.abs(valueRange) * scrambleIntensity
        const currentValue = startValue + valueRange * progress + randomOffset
        setDisplayValue(currentValue)
      } else {
        // Smooth transition phase
        const easeProgress = easeOutCubic(progress)
        const currentValue = startValue + valueRange * easeProgress
        setDisplayValue(currentValue)
      }

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      } else {
        setDisplayValue(endValue)
        setIsAnimating(false)
        prevValueRef.current = endValue
      }
    }

    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current)
    }

    frameRef.current = requestAnimationFrame(animate)

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current)
      }
    }
  }, [value, duration, scramble])

  const formattedValue = displayValue.toFixed(decimals)

  return (
    <span
      className={`${className} ${isAnimating ? "animate-pulse-subtle" : ""}`}
      style={{
        display: "inline-block",
        minWidth: "fit-content",
      }}
    >
      {prefix}
      {formattedValue}
      {suffix}
    </span>
  )
}

// Easing function for smooth animation
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}
