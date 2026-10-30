'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { eveningTimeline } from './timeline-data'

const colors = ['var(--foreground)', 'var(--chart-3)', 'var(--chart-2)']
const dashes = [undefined, '6 4', '2 4']

export function ActivityTimeline({ detections, years = [] }: {
  detections: Array<{ timestamp: string }>; years?: number[]
}) {
  const { slots, series } = eveningTimeline(detections)
  const max = Math.max(5, ...series.flatMap(s => s.counts))
  const ceiling = Math.ceil(max / 5) * 5
  const width = Math.max(480, slots.length * 28)
  const x = (i: number) => 24 + i * (width - 48) / Math.max(1, slots.length - 1)
  const y = (count: number) => 176 - count / ceiling * 160
  const styleIndex = (year: number) => Math.max(0, (years.length ? years : series.map(s => s.year)).indexOf(year))

  return <Card className="analytics-panel min-w-0">
    <CardHeader>
      <CardTitle>Activity Timeline</CardTitle>
      <CardDescription>Detections per 15 minutes · aligned by time of evening</CardDescription>
      <div className="flex flex-wrap gap-x-5 gap-y-2 pt-3" aria-label="Timeline years">
        {series.map(s => <span key={s.year} className="inline-flex items-center gap-2 text-xs">
          <svg width="24" height="8" aria-hidden="true"><line x1="0" x2="24" y1="4" y2="4"
            stroke={colors[styleIndex(s.year) % colors.length]} strokeWidth="2" strokeDasharray={dashes[styleIndex(s.year) % dashes.length]} /></svg>
          {s.year}
        </span>)}
      </div>
    </CardHeader>
    <CardContent>
      {!series.length ? <p className="h-56 flex items-center justify-center text-sm text-muted-foreground">No activity data available</p> :
        <div className="flex">
          <div className="relative w-8 shrink-0 text-[10px] text-muted-foreground" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5].map(i => <span key={i} className="absolute" style={{ top: y(i * ceiling / 5) - 7 }}>{i * ceiling / 5}</span>)}
          </div>
          <div className="overflow-x-auto flex-1" tabIndex={0} role="region" aria-label="Activity by time of evening, scroll for more times">
            <svg width="100%" height="216" viewBox={`0 0 ${width} 216`} style={{ minWidth: width }} role="img" aria-label={`Detections per 15 minutes for ${series.map(s => s.year).join(', ')}`}>
              {[0, 1, 2, 3, 4, 5].map(i => <line key={i} x1="0" x2={width} y1={y(i * ceiling / 5)} y2={y(i * ceiling / 5)} stroke="var(--border)" strokeOpacity=".5" />)}
              {series.map(s => <g key={s.year} stroke={colors[styleIndex(s.year) % colors.length]}>
                <polyline points={s.counts.map((count, i) => `${x(i)},${y(count)}`).join(' ')} fill="none" strokeWidth="2" strokeLinejoin="round" strokeDasharray={dashes[styleIndex(s.year) % dashes.length]} />
                {s.counts.map((count, i) => count > 0 && <circle key={i} cx={x(i)} cy={y(count)} r="3" fill="var(--background)"><title>{s.year} · {slots[i].label} · {count} detections</title></circle>)}
              </g>)}
              {slots.map((slot, i) => i % 4 === 0 && <text key={slot.slot} x={x(i)} y="202" textAnchor="middle" fill="var(--muted-foreground)" fontSize="9">{slot.label}</text>)}
            </svg>
          </div>
        </div>}
    </CardContent>
  </Card>
}
