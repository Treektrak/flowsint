import { memo } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '../ui/dialog'
import { DynamicForm } from '../sketches/dynamic-form'
import { useTranslation } from 'react-i18next'

interface TestFlowProps {
  open: boolean
  setOpen: (open: boolean) => void // This should accept a boolean parameter
  loading: boolean
  type: string
  onSubmit: (data: any) => Promise<void>
}

const TestFlow = memo(({ open, setOpen, type, loading, onSubmit }: TestFlowProps) => {
  const { t } = useTranslation()
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogTitle>{t('flows.testFlow')}</DialogTitle>
        <DialogDescription>{t('flows.fillRequiredData')}</DialogDescription>
        <DynamicForm currentNodeType={type} isForm={true} loading={loading} onSubmit={onSubmit} />
      </DialogContent>
    </Dialog>
  )
})

export default TestFlow
