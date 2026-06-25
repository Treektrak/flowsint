import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useConfirm } from '@/components/use-confirm-dialog'
import { cn } from '@/lib/utils'
import { useGraphControls } from '@/stores/graph-controls-store'
import { useGraphStore } from '@/stores/graph-store'
import {
  FunnelPlus,
  GitFork,
  GitPullRequestArrow,
  Maximize,
  Merge,
  Minus,
  RotateCw,
  ZoomIn,
  Focus,
  Download,
  LassoSelect,
  ChevronDown,
  SquareDashed,
  Sparkles
} from 'lucide-react'
import { memo, useCallback, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import Filters from './filters/filters'
import { SaveStatusIndicator } from './save-status-indicator'
import { Separator } from '../ui/separator'
import { ViewToggle } from './view-toggle'
import { NetworkIcon } from '../icons/network'
import { useKeyboard } from '@/hooks/use-keyboard'
import { usePermissions } from '@/hooks/use-can'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { sketchService } from '@/api/sketch-service'
import { downloadAgentReport, listModels, type ProviderModels } from '@/api/agent-service'
import { useParams } from '@tanstack/react-router'
import { exportToPNG } from './graph/utils/export-to-png'
import { PathFinder } from './graph/actions/path-finder'

// Tooltip wrapper component to avoid repetition
export const ToolbarButton = memo(function ToolbarButton({
  icon,
  tooltip,
  onClick,
  disabled = false,
  badge = null,
  toggled = false,
  showLabel = false
}: {
  icon: React.ReactNode
  tooltip: string | React.ReactNode
  onClick?: () => void
  disabled?: boolean
  badge?: number | null
  toggled?: boolean | null
  showLabel?: boolean
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div>
          <Button
            onClick={onClick}
            disabled={disabled}
            variant="ghost"
            size={showLabel ? 'sm' : 'icon'}
            className={cn(
              'h-7 relative items-center shadow-none',
              !showLabel && 'w-7',
              toggled &&
                'bg-primary/30 border-primary/40 text-primary hover:bg-primary/40 hover:text-primary'
            )}
          >
            {icon} {showLabel && <span className="hidden md:block">{tooltip}</span>}
            {badge && (
              <span className="absolute -top-1 -right-2 !z-[500] bg-primary text-white text-[10px] rounded-full w-auto min-w-4.5 h-4.5 p-1 flex items-center justify-center">
                {badge}
              </span>
            )}
          </Button>
        </div>
      </TooltipTrigger>
      <TooltipContent>{tooltip}</TooltipContent>
    </Tooltip>
  )
})

const FloatingBar = ({
  children,
  className
}: {
  children: React.ReactNode
  className?: string
}) => (
  <div
    className={cn(
      'absolute z-50 flex items-center gap-0.5 rounded-lg border bg-card p-1',
      className
    )}
  >
    {children}
  </div>
)

export const Toolbar = memo(function Toolbar({ isLoading }: { isLoading: boolean }) {
  const { t } = useTranslation()
  const { confirm } = useConfirm()
  const { canEdit } = usePermissions()
  const { id: sketchId } = useParams({ strict: false })
  const view = useGraphControls((s) => s.view)
  const setView = useGraphControls((s) => s.setView)
  const zoomToFit = useGraphControls((s) => s.zoomToFit)
  const zoomToSelection = useGraphControls((s) => s.zoomToSelection)
  const zoomIn = useGraphControls((s) => s.zoomIn)
  const zoomOut = useGraphControls((s) => s.zoomOut)
  const regenerateLayout = useGraphControls((s) => s.regenerateLayout)
  const refetchGraph = useGraphControls((s) => s.refetchGraph)
  const isSelectorModeActive = useGraphControls((s) => s.isSelectorModeActive)
  const setIsSelectorModeActive = useGraphControls((s) => s.setIsSelectorModeActive)
  const selectionMode = useGraphControls((s) => s.selectionMode)
  const setSelectionMode = useGraphControls((s) => s.setSelectionMode)
  const selectedNodes = useGraphStore((s) => s.selectedNodes)
  const setOpenAddRelationDialog = useGraphStore((state) => state.setOpenAddRelationDialog)
  const setOpenMergeDialog = useGraphStore((state) => state.setOpenMergeDialog)
  const filters = useGraphStore((s) => s.filters)

  useKeyboard(
    's',
    () => setIsSelectorModeActive(true),
    () => setIsSelectorModeActive(false)
  )

  const handleRefresh = useCallback(() => {
    try {
      refetchGraph()
    } catch (error) {
      toast.error(t('graphToolbar.refreshFailed'))
    }
  }, [refetchGraph])

  const handleApplyForceLayout = useCallback(async () => {
    const confirmed = await confirm({
      title: t('graphToolbar.forceLayoutConfirmTitle'),
      message: t('graphToolbar.forceLayoutConfirmMessage')
    })

    if (!confirmed) {
      return
    }
    try {
      regenerateLayout('force')
      toast.success(t('graphToolbar.forceLayoutSuccess'))
    } catch (error) {
      toast.error(
        t('graphToolbar.applyLayoutFailed', {
          error: error instanceof Error ? error.message : t('graphToolbar.unknownError')
        })
      )
    }
  }, [confirm, regenerateLayout, t])

  const handleApplyHierarchyLayout = useCallback(async () => {
    const confirmed = await confirm({
      title: t('graphToolbar.hierarchyLayoutConfirmTitle'),
      message: t('graphToolbar.hierarchyLayoutConfirmMessage')
    })

    if (!confirmed) {
      return
    }
    try {
      regenerateLayout('hierarchy')
      toast.success(t('graphToolbar.hierarchyLayoutSuccess'))
    } catch (error) {
      toast.error(
        t('graphToolbar.applyLayoutFailed', {
          error: error instanceof Error ? error.message : t('graphToolbar.unknownError')
        })
      )
    }
  }, [confirm, regenerateLayout, t])

  const handleOpenAddRelationDialog = useCallback(() => {
    setOpenAddRelationDialog(true)
  }, [setOpenAddRelationDialog])

  const handleOpenMergeDialog = useCallback(() => {
    setOpenMergeDialog(true)
  }, [setOpenMergeDialog])

  const handleToggleSelector = useCallback(() => {
    setIsSelectorModeActive(!isSelectorModeActive)
  }, [setIsSelectorModeActive, isSelectorModeActive])

  const handleSelectMode = useCallback(
    (mode: 'lasso' | 'rectangle') => {
      setSelectionMode(mode)
      if (!isSelectorModeActive) {
        setIsSelectorModeActive(true)
      }
    },
    [setSelectionMode, isSelectorModeActive, setIsSelectorModeActive]
  )

  const handleExport = useCallback(
    async (format: 'json' | 'png') => {
      if (!sketchId) return
      try {
        if (format === 'png') {
          await exportToPNG('null', 'null')
        } else {
          await sketchService.exportSketch(sketchId, format)
        }
        toast.success(t('graphToolbar.exportSuccess', { format: format.toUpperCase() }))
      } catch (error) {
        toast.error(
          t('graphToolbar.exportFailed', {
            error: error instanceof Error ? error.message : t('graphToolbar.unknownError')
          })
        )
      }
    },
    [sketchId, exportToPNG, t]
  )

  const [isReporting, setIsReporting] = useState(false)
  const [providers, setProviders] = useState<ProviderModels[]>([])
  useEffect(() => {
    listModels()
      .then((m) => setProviders(m.filter((p) => p.has_key)))
      .catch(() => setProviders([]))
  }, [])

  const handleReport = useCallback(
    async (provider?: string, model?: string) => {
      if (!sketchId || isReporting) return
      setIsReporting(true)
      const pending = toast.loading(t('graphToolbar.reportGenerating'))
      try {
        const filename = await downloadAgentReport(sketchId, '', { provider, model })
        toast.success(t('graphToolbar.reportReady', { filename }), { id: pending })
      } catch (error) {
        toast.error(
          t('graphToolbar.reportFailed', {
            error: error instanceof Error ? error.message : t('graphToolbar.unknownError')
          }),
          { id: pending }
        )
      } finally {
        setIsReporting(false)
      }
    },
    [sketchId, isReporting, t]
  )

  const areExactlyTwoSelected = selectedNodes.length === 2
  const areMergeable =
    selectedNodes.length > 1 && selectedNodes.every((n) => n.nodeType === selectedNodes[0].nodeType)
  const hasFilters = !(
    filters.types.every((t) => t.checked) || filters.types.every((t) => !t.checked)
  )

  return (
    <>
      {/* Bottom-left: Zoom controls */}
      {(view === 'graph' || view === 'map') && (
        <FloatingBar className="bottom-3 left-3">
          <ToolbarButton
            icon={<ZoomIn className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.zoomIn')}
            onClick={zoomIn}
            disabled={(view !== 'graph' && view !== 'map') || isSelectorModeActive || !zoomIn}
          />
          <ToolbarButton
            icon={<Minus className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.zoomOut')}
            onClick={zoomOut}
            disabled={(view !== 'graph' && view !== 'map') || isSelectorModeActive}
          />
          <ToolbarButton
            icon={<Maximize className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.fitToView')}
            onClick={zoomToFit}
            disabled={(view !== 'graph' && view !== 'map') || isSelectorModeActive}
          />
          <ToolbarButton
            icon={<Focus className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.zoomToSelection')}
            onClick={zoomToSelection}
            disabled={view !== 'graph' || isSelectorModeActive || selectedNodes.length < 2}
          />
        </FloatingBar>
      )}

      {/* Left middle: Selection, Actions & Layout */}
      {view === 'graph' && (
        <FloatingBar className="left-3 top-1/2 -translate-y-1/2 flex-col">
          <div className="flex flex-col items-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleToggleSelector}
                  disabled={view !== 'graph'}
                  className={cn(
                    'h-7 w-7 rounded relative items-center shadow-none',
                    isSelectorModeActive &&
                      'bg-primary/30 border-primary/40 text-primary hover:bg-primary/40 hover:text-primary'
                  )}
                >
                  {selectionMode === 'lasso' ? (
                    <LassoSelect className="h-4 w-4 opacity-70" />
                  ) : (
                    <SquareDashed className="h-4 w-4 opacity-70" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{t('graphToolbar.selectHoldS')}</TooltipContent>
            </Tooltip>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={view !== 'graph'}
                        className={cn(
                          'h-3! w-5 px-0 rounded relative items-center shadow-none',
                          isSelectorModeActive &&
                            'bg-primary/30 border-primary/40 text-primary hover:bg-primary/40 hover:text-primary'
                        )}
                      >
                        <ChevronDown className="h-3 w-3 opacity-50" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>{t('graphToolbar.selectionMode')}</TooltipContent>
                  </Tooltip>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="min-w-[140px]">
                <DropdownMenuItem
                  onClick={() => handleSelectMode('lasso')}
                  className={cn(selectionMode === 'lasso' && 'bg-accent')}
                >
                  <LassoSelect className="h-4 w-4 mr-2" />
                  {t('graphToolbar.lasso')}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => handleSelectMode('rectangle')}
                  className={cn(selectionMode === 'rectangle' && 'bg-accent')}
                >
                  <SquareDashed className="h-4 w-4 mr-2" />
                  {t('graphToolbar.rectangle')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <Separator className="w-full" />
          <ToolbarButton
            icon={<GitPullRequestArrow className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.connect')}
            onClick={handleOpenAddRelationDialog}
            disabled={!canEdit || !areExactlyTwoSelected}
            badge={areExactlyTwoSelected ? 2 : null}
          />
          <ToolbarButton
            icon={<Merge className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.merge')}
            onClick={handleOpenMergeDialog}
            disabled={!canEdit || !areMergeable}
            badge={areMergeable ? selectedNodes.length : null}
          />
          <PathFinder />
          <Separator className="w-full" />
          <ToolbarButton
            icon={<NetworkIcon className="h-4 w-4 opacity-70" />}
            tooltip={t('graphToolbar.forceLayout')}
            onClick={handleApplyForceLayout}
            disabled={!canEdit || isLoading || view !== 'graph'}
          />
          <ToolbarButton
            icon={<GitFork strokeWidth={1.4} className="h-4 w-4 opacity-70 rotate-180" />}
            tooltip={t('graphToolbar.hierarchyLayout')}
            onClick={handleApplyHierarchyLayout}
            disabled={!canEdit || isLoading || view !== 'graph'}
          />
        </FloatingBar>
      )}

      <FloatingBar className="top-3 left-1/2 -translate-x-1/2">
        <ViewToggle view={view} setView={setView} />
        <Separator orientation="vertical" className="h-5" />
        <Filters>
          <ToolbarButton
            disabled={isLoading}
            icon={<FunnelPlus className={cn('h-4 w-4 opacity-70')} />}
            tooltip={t('graphToolbar.filters')}
            toggled={hasFilters}
          />
        </Filters>
      </FloatingBar>

      {/* Top right: Status, Export, Reload */}
      <FloatingBar className="top-3 right-3">
        <SaveStatusIndicator />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    disabled={isLoading}
                    className="h-7 w-7 relative items-center shadow-none"
                  >
                    <Download className="h-4 w-4 opacity-70" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{t('graphToolbar.export')}</TooltipContent>
              </Tooltip>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-[140px]">
            <DropdownMenuItem onClick={() => handleExport('json')}>
              {t('graphToolbar.exportAsJson')}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('png')}>
              {t('graphToolbar.exportAsPng')}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleReport()} disabled={isReporting}>
              <Sparkles className="h-4 w-4 mr-2 opacity-70" />
              {isReporting ? t('graphToolbar.reportGenerating') : t('graphToolbar.aiReport')}
            </DropdownMenuItem>
            {providers.map((p) => (
              <DropdownMenuItem
                key={p.provider}
                disabled={isReporting}
                onClick={() => handleReport(p.provider, p.models[0])}
                className="pl-8 text-xs text-muted-foreground"
              >
                {t('graphToolbar.reportWith', { model: `${p.provider} · ${p.models[0]}` })}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <ToolbarButton
          onClick={handleRefresh}
          disabled={isLoading}
          icon={<RotateCw className={cn('h-4 w-4 opacity-70', isLoading && 'animate-spin')} />}
          tooltip={t('graphToolbar.refresh')}
        />
      </FloatingBar>
    </>
  )
})
