import { useCallback, useState, memo } from 'react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
  SheetTrigger
} from '@/components/ui/sheet'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { useLaunchEnricher } from '@/hooks/use-launch-enricher'
import { useLaunchFlow } from '@/hooks/use-launch-flow'
import { formatDistanceToNow } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { enricherService } from '@/api/enricher-service'
import { flowService } from '@/api/flow-service'
import { Link, useParams } from '@tanstack/react-router'
import { capitalizeFirstLetter } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, FileCode2, Zap, PlusIcon, GitBranch, FileX, Sparkles } from 'lucide-react'
import { Enricher, Flow } from '@/types'
import { useTranslation } from 'react-i18next'

const LaunchEnricherOrFlowPanel = memo(
  ({ values, type, children, disabled }: { values: string[]; type: string; children?: React.ReactNode, disabled?: boolean }) => {
    const { t } = useTranslation()
    const { launchEnricher } = useLaunchEnricher()
    const { launchFlow } = useLaunchFlow()
    const { id: sketch_id } = useParams({ strict: false })
    const [isOpen, setIsOpen] = useState(false)
    const [selectedEnricher, setSelectedEnricher] = useState<Enricher | Flow | null>(null)
    const [activeTab, setActiveTab] = useState('enrichers')
    const [enrichersSearchQuery, setEnrichersSearchQuery] = useState('')
    const [flowsSearchQuery, setFlowsSearchQuery] = useState('')

    const { data: enrichers, isLoading: isLoadingEnrichers } = useQuery({
      queryKey: ['enrichers', type],
      queryFn: () => enricherService.get(capitalizeFirstLetter(type))
    })

    const { data: flows, isLoading: isLoadingFlows } = useQuery({
      queryKey: ['flows', type],
      queryFn: () => flowService.get(capitalizeFirstLetter(type))
    })

    const filteredEnrichers =
      enrichers?.filter((enricher: Enricher) => {
        if (!enrichersSearchQuery.trim()) return true
        const query = enrichersSearchQuery.toLowerCase().trim()
        const matchesName = enricher.name?.toLowerCase().includes(query)
        const matchesDescription = enricher.description?.toLowerCase().includes(query)
        return matchesName || matchesDescription
      }) || []

    const filteredFlows =
      flows?.filter((enricher: Flow) => {
        if (!flowsSearchQuery.trim()) return true
        const query = flowsSearchQuery.toLowerCase().trim()
        const matchesName = enricher.name?.toLowerCase().includes(query)
        const matchesDescription = enricher.description?.toLowerCase().includes(query)
        return matchesName || matchesDescription
      }) || []

    const handleCloseModal = useCallback(() => {
      setIsOpen(false)
    }, [])

    const handleSelectEnricher = useCallback((enricher: Enricher | Flow) => {
      setSelectedEnricher(enricher)
    }, [])

    const handleLaunchPanel = useCallback(() => {
      if (selectedEnricher) {
        // Check if it's an Enricher or Flow based on the active tab
        if (activeTab === 'enrichers') {
          // For enrichers, use name
          launchEnricher(values, (selectedEnricher as Enricher).name, sketch_id)
        } else {
          // For flows, use id
          launchFlow(values, (selectedEnricher as Flow).id, sketch_id)
        }
        handleCloseModal()
      }
    }, [selectedEnricher, activeTab, launchEnricher, launchFlow, values, sketch_id])

    if (disabled) return (
      <>{children}</>
    )
    return (
      <div>
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger disabled={disabled} asChild>
            <div>{children}</div>
          </SheetTrigger>
          <SheetContent className="sm:max-w-xl">
            <SheetHeader>
              <SheetTitle>{t('enrichers.selectEnricherTitle')}</SheetTitle>
              <SheetDescription>{t('enrichers.selectEnricherDescription')}</SheetDescription>
            </SheetHeader>

            {/* Tabs */}
            <div className="px-4 py-2 border-b border-border">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="w-full">
                  <TabsTrigger
                    value="enrichers"
                    className="flex-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Zap className="h-3 w-3 mr-1" />
                    {t('enrichers.tabEnrichers')}
                  </TabsTrigger>
                  <TabsTrigger
                    value="flows"
                    className="flex-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <FileCode2 className="h-3 w-3 mr-1" />
                    {t('enrichers.tabFlows')}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Tab Content */}
            <Tabs value={activeTab} className="flex-1 flex flex-col min-h-0">
              {/* Enrichers Tab */}
              <TabsContent value="enrichers" className="flex-1 flex flex-col min-h-0 mt-0">
                {/* Enrichers Search */}
                <div className="px-4 py-2 border-b border-border">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                    <Input
                      type="search"
                      placeholder={t('enrichers.searchEnrichersPlaceholder')}
                      value={enrichersSearchQuery}
                      onChange={(e) => setEnrichersSearchQuery(e.target.value)}
                      className="h-8 pl-7 text-sm"
                    />
                  </div>
                </div>

                {/* Enrichers List */}
                <div className="p-4 grow overflow-auto">
                  <RadioGroup
                    value={
                      selectedEnricher && 'name' in selectedEnricher
                        ? selectedEnricher.name
                        : undefined
                    }
                    className="space-y-3"
                  >
                    {isLoadingEnrichers ? (
                      // Skeleton loading state
                      Array.from({ length: 3 }).map((_, index) => (
                        <Card key={index} className="border py-1">
                          <CardHeader className="p-4">
                            <div className="flex flex-col space-y-4">
                              <div className="flex items-center gap-3">
                                <Skeleton className="h-4 w-4 rounded-full" />
                                <Skeleton className="h-5 w-32" />
                              </div>
                              <div className="pl-7 space-y-2">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-4 w-3/4" />
                              </div>
                              <div className="flex flex-col space-y-1 pl-7">
                                <Skeleton className="h-3 w-24" />
                                <Skeleton className="h-3 w-20" />
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      ))
                    ) : filteredEnrichers.length > 0 ? (
                      filteredEnrichers.map((enricher: Enricher) => (
                        <Card
                          key={enricher.name}
                          className={`cursor-pointer border py-1 transition-all ${selectedEnricher &&
                            'name' in selectedEnricher &&
                            selectedEnricher.name === enricher.name
                            ? 'border-primary bg-primary/5'
                            : 'hover:border-primary/50'
                            }`}
                          onClick={() => handleSelectEnricher(enricher)}
                        >
                          <CardHeader className="p-4">
                            <div className="flex flex-col space-y-4">
                              <div className="flex items-center gap-3">
                                <RadioGroupItem value={enricher.name} id={enricher.name} />
                                <CardTitle className="text-base">{enricher.name}</CardTitle>
                              </div>

                              {enricher.description && (
                                <CardDescription className="text-sm pl-7">
                                  {enricher.description || t('enrichers.noDescriptionAvailable')}
                                </CardDescription>
                              )}
                            </div>
                          </CardHeader>
                        </Card>
                      ))
                    ) : (
                      <div className="p-8 text-center space-y-6">
                        <div className="flex justify-center">
                          <div className="p-4 rounded-full bg-muted/50">
                            {enrichersSearchQuery ? (
                              <FileX className="h-8 w-8 text-muted-foreground" />
                            ) : (
                              <FileCode2 className="h-8 w-8 text-muted-foreground" />
                            )}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-lg font-semibold">
                            {enrichersSearchQuery
                              ? t('enrichers.noEnrichersFound')
                              : t('enrichers.noEnrichersAvailable')}
                          </h3>
                          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                            {enrichersSearchQuery
                              ? t('enrichers.noEnrichersFoundHint')
                              : t('enrichers.enrichersEmptyDescription')}
                          </p>
                        </div>
                        {!enrichersSearchQuery && (
                          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                            <Sparkles className="h-3 w-3" />
                            <span>{t('enrichers.enrichersWillAppear')}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </RadioGroup>
                </div>
              </TabsContent>

              {/* Flows Tab */}
              <TabsContent value="flows" className="flex-1 flex flex-col min-h-0 mt-0">
                {/* Flows Search */}
                <div className="px-4 py-2 border-b border-border">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                    <Input
                      type="search"
                      placeholder={t('enrichers.searchFlowsPlaceholder')}
                      value={flowsSearchQuery}
                      onChange={(e) => setFlowsSearchQuery(e.target.value)}
                      className="h-8 pl-7 text-sm"
                    />
                  </div>
                </div>

                {/* Flows List */}
                <div className="p-4 grow overflow-auto">
                  <RadioGroup
                    value={
                      selectedEnricher && 'id' in selectedEnricher
                        ? selectedEnricher.id
                        : undefined
                    }
                    className="space-y-3"
                  >
                    {isLoadingFlows ? (
                      // Skeleton loading state
                      Array.from({ length: 3 }).map((_, index) => (
                        <Card key={index} className="border py-1">
                          <CardHeader className="p-4">
                            <div className="flex flex-col space-y-4">
                              <div className="flex items-center gap-3">
                                <Skeleton className="h-4 w-4 rounded-full" />
                                <Skeleton className="h-5 w-32" />
                              </div>
                              <div className="pl-7 space-y-2">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-4 w-3/4" />
                              </div>
                              <div className="flex flex-col space-y-1 pl-7">
                                <Skeleton className="h-3 w-24" />
                                <Skeleton className="h-3 w-20" />
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      ))
                    ) : filteredFlows.length > 0 ? (
                      filteredFlows.map((flow: Flow) => (
                        <Card
                          key={flow.id}
                          className={`cursor-pointer border py-1 transition-all ${selectedEnricher &&
                            'id' in selectedEnricher &&
                            selectedEnricher.id === flow.id
                            ? 'border-primary bg-primary/5'
                            : 'hover:border-primary/50'
                            }`}
                          onClick={() => handleSelectEnricher(flow)}
                        >
                          <CardHeader className="p-4">
                            <div className="flex flex-col space-y-4">
                              <div className="flex items-center gap-3">
                                <RadioGroupItem value={flow.id} id={flow.id} />
                                <CardTitle className="text-base">{flow.name}</CardTitle>
                              </div>

                              {flow.description && (
                                <CardDescription className="text-sm pl-7">
                                  {flow.description || t('enrichers.noDescriptionAvailable')}
                                </CardDescription>
                              )}

                              <div className="flex flex-col space-y-1 text-xs text-muted-foreground pl-7">
                                <div>
                                  {t('enrichers.createdAt', {
                                    time: formatDistanceToNow(flow.created_at, { addSuffix: true })
                                  })}
                                </div>
                                <div>
                                  {t('enrichers.updatedAt', {
                                    time: formatDistanceToNow(flow.last_updated_at, {
                                      addSuffix: true
                                    })
                                  })}
                                </div>
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      ))
                    ) : (
                      <div className="p-8 text-center space-y-6">
                        <div className="flex justify-center">
                          <div className="p-4 rounded-full bg-muted/50">
                            {flowsSearchQuery ? (
                              <FileX className="h-8 w-8 text-muted-foreground" />
                            ) : (
                              <GitBranch className="h-8 w-8 text-muted-foreground" />
                            )}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-lg font-semibold">
                            {flowsSearchQuery ? t('enrichers.noFlowsFound') : t('enrichers.noFlowsAvailable')}
                          </h3>
                          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                            {flowsSearchQuery
                              ? t('enrichers.noFlowsFoundHint')
                              : t('enrichers.flowsEmptyDescription')}
                          </p>
                        </div>
                        {!flowsSearchQuery && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                              <Zap className="h-3 w-3" />
                              <span>{t('enrichers.createFirstFlowHint')}</span>
                            </div>
                            <Link to="/dashboard/flows">
                              <Button className="gap-2">
                                <PlusIcon className="h-4 w-4" />
                                {t('enrichers.createFirstFlow')}
                              </Button>
                            </Link>
                          </div>
                        )}
                      </div>
                    )}
                  </RadioGroup>
                </div>
              </TabsContent>
            </Tabs>

            <SheetFooter>
              <Button variant="outline" onClick={handleCloseModal} className="mr-2">
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleLaunchPanel}
                disabled={!selectedEnricher}
                className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary"
              >
                {t('enrichers.launchEnricher')}
              </Button>
            </SheetFooter>
          </SheetContent>
        </Sheet>
      </div>
    )
  }
)

export default LaunchEnricherOrFlowPanel
