'use client'

import { useEffect, useState, useRef } from 'react'

interface AnimatedNumberProps {
  value: string | number
  className?: string
  scrambleDuration?: number
}

export function AnimatedNumber({
  value,
  className = '',
  scrambleDuration = 800
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(String(value))
  const [isAnimating, setIsAnimating] = useState(false)
  const previousValue = useRef<string | null>(null)
  const isMounted = useRef(false)

  useEffect(() => {
    const newValue = String(value)

    // On initial mount, animate from nothing
    if (!isMounted.current) {
      isMounted.current = true
      previousValue.current = newValue
      // Trigger animation on mount
    } else {
      // Only animate if the value actually changed
      if (newValue === previousValue.current) {
        return
      }
    }

    setIsAnimating(true)
    const startTime = Date.now()
    const oldValue = previousValue.current

    // Characters to use for scrambling (numbers, some special chars)
    const scrambleChars = '0123456789$,.'

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / scrambleDuration, 1)

      if (progress < 1) {
        // Scramble phase - gradually reveal the correct digits
        const scrambled = newValue.split('').map((char, index) => {
          // Non-numeric characters (like $, %, commas) stay the same
          if (!/\d/.test(char) && char !== '.') {
            return char
          }

          // Gradually lock in digits from left to right
          const lockProgress = Math.max(0, (progress - (index * 0.1)) * 2)

          if (lockProgress >= 1) {
            return char // This digit is locked in
          }

          // Still scrambling this digit
          const randomChar = scrambleChars[Math.floor(Math.random() * scrambleChars.length)]
          return randomChar
        }).join('')

        setDisplayValue(scrambled)
        requestAnimationFrame(animate)
      } else {
        // Animation complete
        setDisplayValue(newValue)
        setIsAnimating(false)
        previousValue.current = newValue
      }
    }

    requestAnimationFrame(animate)
  }, [value, scrambleDuration])

  return (
    <span
      className={`${className} ${isAnimating ? 'animate-number-flip' : ''}`}
      style={{
        display: 'inline-block',
        fontVariantNumeric: 'tabular-nums', // Ensures consistent digit width
      }}
    >
      {displayValue}
    </span>
  )
}
