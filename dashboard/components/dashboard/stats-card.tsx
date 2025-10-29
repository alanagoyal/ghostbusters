import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AnimatedNumber } from '@/components/ui/animated-number'
import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  description?: string
  icon?: LucideIcon
  trend?: {
    value: number
    label: string
  }
}

export function StatsCard({ title, value, description, icon: Icon, trend }: StatsCardProps) {
  const numericValue = typeof value === 'string' ? parseFloat(value) || 0 : value
  const isNumeric = typeof value === 'number' || !isNaN(numericValue)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {isNumeric ? (
            <AnimatedNumber value={numericValue} decimals={0} />
          ) : (
            value
          )}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            <span className="text-xs font-medium text-muted-foreground">
              <AnimatedNumber
                value={trend.value}
                decimals={1}
                prefix={trend.value > 0 ? '+' : ''}
                suffix="%"
                className="text-xs font-medium text-muted-foreground"
              />
            </span>
            <span className="text-xs text-muted-foreground">{trend.label}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
