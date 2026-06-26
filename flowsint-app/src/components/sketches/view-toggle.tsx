import { List, ArrowRightLeft, MapPin } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { NetworkIcon } from '../icons/network'
import { useTranslation } from 'react-i18next'

interface ViewToggleProps {
  view: 'graph' | 'table' | 'relationships' | 'map'
  setView: (view: 'graph' | 'table' | 'relationships' | 'map') => void
}

const views = [
  { value: 'graph', icon: NetworkIcon, labelKey: 'misc2.viewGraph' },
  { value: 'table', icon: List, labelKey: 'misc2.viewTable' },
  { value: 'relationships', icon: ArrowRightLeft, labelKey: 'misc2.viewRelationships' },
  { value: 'map', icon: MapPin, labelKey: 'misc2.viewMap' }
] as const

export function ViewToggle({ view, setView }: ViewToggleProps) {
  const { t } = useTranslation()
  return (
    <ToggleGroup
      type="single"
      value={view}
      onValueChange={(v) => v && setView(v as typeof view)}
    >
      {views.map(({ value, icon: Icon, labelKey }) => (
        <Tooltip key={value}>
          <TooltipTrigger asChild>
            <ToggleGroupItem
              value={value}
              aria-label={t(labelKey)}
              className="h-7 w-7 p-0"
            >
              <Icon className="h-4 w-4" />
            </ToggleGroupItem>
          </TooltipTrigger>
          <TooltipContent>{t(labelKey)}</TooltipContent>
        </Tooltip>
      ))}
    </ToggleGroup>
  )
}
