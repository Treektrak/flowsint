import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Panel } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { toast } from 'sonner'
import { flowService } from '@/api/flow-service'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/api/query-keys'
import type { Flow } from '@/types/flow'
import { useTranslation } from 'react-i18next'

interface FlowNamePanelProps {
  flow?: Flow
  onUpdate?: (updates: Partial<Flow>) => void
  disabled?: boolean
}

export const FlowNamePanel = ({ flow, onUpdate, disabled = false }: FlowNamePanelProps) => {
  const { t } = useTranslation()
  const [isEditingName, setIsEditingName] = useState(false)
  const [isEditingDesc, setIsEditingDesc] = useState(false)
  const [name, setName] = useState(flow?.name || t('flows.defaultFlowNameShort'))
  const [description, setDescription] = useState(flow?.description || '')
  const [isSaving, setIsSaving] = useState(false)
  const nameInputRef = useRef<HTMLInputElement>(null)
  const descInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  // Update flow mutation
  const updateFlowMutation = useMutation({
    mutationFn: ({ flowId, body }: { flowId: string; body: BodyInit }) =>
      flowService.update(flowId, body),
    onSuccess: (data, variables) => {
      if (onUpdate) {
        onUpdate(variables.body as Partial<Flow>)
      }
      // Invalidate the flow detail query
      queryClient.invalidateQueries({
        queryKey: queryKeys.flows.detail(variables.flowId)
      })
      toast.success(t('flows.flowUpdated'))
    },
    onError: (error) => {
      toast.error(
        t('flows.flowUpdateFailed') +
          ' ' +
          (error instanceof Error ? error.message : t('flows.unknownError'))
      )
    }
  })

  useEffect(() => {
    if (flow) {
      setName(flow.name || t('flows.defaultFlowNameShort'))
      setDescription(flow.description || '')
    }
  }, [flow])

  useEffect(() => {
    if (isEditingName && nameInputRef.current) {
      nameInputRef.current.focus()
    }
  }, [isEditingName])

  useEffect(() => {
    if (isEditingDesc && descInputRef.current) {
      descInputRef.current.focus()
    }
  }, [isEditingDesc])

  const handleSaveField = async (field: 'name' | 'description', value: string) => {
    if (!flow?.id) return

    const trimmedValue = value.trim()
    if (field === 'name' && trimmedValue === '') return

    if (
      (field === 'name' && trimmedValue === flow.name) ||
      (field === 'description' && trimmedValue === flow.description)
    ) {
      field === 'name' ? setIsEditingName(false) : setIsEditingDesc(false)
      return
    }

    setIsSaving(true)
    try {
      const updates = { [field]: trimmedValue }
      await updateFlowMutation.mutateAsync({
        flowId: flow.id,
        body: JSON.stringify(updates)
      })
    } catch (error) {
      // Revert local state on error
      if (field === 'name') {
        setName(flow.name)
      } else {
        setDescription(flow.description || '')
      }
    } finally {
      setIsSaving(false)
      field === 'name' ? setIsEditingName(false) : setIsEditingDesc(false)
    }
  }

  const handleKeyDown = (
    e: KeyboardEvent<HTMLInputElement>,
    field: 'name' | 'description',
    value: string
  ) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSaveField(field, value)
    } else if (e.key === 'Escape') {
      if (field === 'name') {
        setIsEditingName(false)
        setName(flow?.name || t('flows.defaultFlowNameShort'))
      } else {
        setIsEditingDesc(false)
        setDescription(flow?.description || '')
      }
    }
  }

  return (
    <Panel position="top-left" className="m-4">
      <Card className="px-3 py-2 gap-1 w-sm rounded-mdgap-1">
        {isEditingName ? (
          <input
            ref={nameInputRef}
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => handleSaveField('name', name)}
            onKeyDown={(e) => handleKeyDown(e, 'name', name)}
            disabled={disabled || isSaving}
            className="!text-xl font-semibold bg-transparent border-b border-gray-300 focus:border-primary focus:outline-none !px-1 !py-0.5 w-full"
            placeholder={t('flows.enterFlowName')}
          />
        ) : (
          <h1
            className="text-xl font-semibold cursor-pointer hover:bg-foreground/10 px-1 py-0.5 rounded-mdtransition-colors"
            onClick={() => !disabled && setIsEditingName(true)}
          >
            {name || t('flows.defaultFlowNameShort')}
          </h1>
        )}

        {isEditingDesc ? (
          <input
            ref={descInputRef}
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onBlur={() => handleSaveField('description', description)}
            onKeyDown={(e) => handleKeyDown(e, 'description', description)}
            disabled={disabled || isSaving}
            className="text-sm text-muted-foreground bg-transparent border-b border-gray-300 focus:border-primary focus:outline-none px-1 py-0.5 w-full"
            placeholder={t('flows.addDescription')}
          />
        ) : (
          <p
            className="text-sm text-muted-foreground cursor-pointer hover:bg-foreground/10 px-1 py-0.5 rounded-mdtransition-colors min-h-[1.5rem]"
            onClick={() => !disabled && setIsEditingDesc(true)}
          >
            {description || (
              <span className="italic text-gray-400">{t('flows.addDescription')}</span>
            )}
          </p>
        )}
      </Card>
    </Panel>
  )
}
