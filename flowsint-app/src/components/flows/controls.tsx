import { Button } from '@/components/ui/button'
import { Panel } from '@xyflow/react'
import { Save, Trash2, ZoomIn, ZoomOut, Maximize, LayoutGrid } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { FlowNamePanel } from './flow-name-panel'
import { useTranslation } from 'react-i18next'

interface FlowControlsProps {
  loading: boolean
  handleSaveFlow: () => void
  handleDeleteFlow: () => void
  onLayout: () => void
  fitView: () => void
  zoomIn: () => void
  zoomOut: () => void
  isSaved: boolean
  flow?: any
}

export function FlowControls({
  loading,
  handleSaveFlow,
  handleDeleteFlow,
  onLayout,
  fitView,
  zoomIn,
  zoomOut,
  isSaved,
  flow
}: FlowControlsProps): JSX.Element {
  const { t } = useTranslation()
  return (
    <TooltipProvider>
      <FlowNamePanel flow={flow} />
      <Panel position="bottom-right" className="flex gap-2 mt-28 mr-2 z-40">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="bg-card"
              onClick={handleSaveFlow}
              disabled={loading}
              data-tour-id="save-button"
            >
              <Save className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t('flows.saveFlow')}</p>
          </TooltipContent>
        </Tooltip>

        {isSaved && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="bg-card"
                onClick={handleDeleteFlow}
                disabled={loading}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t('flows.deleteFlow')}</p>
            </TooltipContent>
          </Tooltip>
        )}

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="bg-card"
              onClick={onLayout}
              data-tour-id="layout-button"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t('flows.autoLayout')}</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline" size="icon" className="bg-card" onClick={fitView}>
              <Maximize className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t('flows.fitView')}</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline" size="icon" className="bg-card" onClick={zoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t('flows.zoomIn')}</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline" size="icon" className="bg-card" onClick={zoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t('flows.zoomOut')}</p>
          </TooltipContent>
        </Tooltip>
      </Panel>
    </TooltipProvider>
  )
}
