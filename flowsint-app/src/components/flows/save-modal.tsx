import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useKeyboardShortcut } from '@/hooks/use-keyboard-shortcut'
import { useTranslation } from 'react-i18next'

interface SaveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (name: string, description: string) => void
  isLoading: boolean
  initialName?: string
  initialDescription?: string
}

export function SaveModal({ open, onOpenChange, onSave, isLoading, initialName, initialDescription }: SaveModalProps) {
  const { t } = useTranslation()
  const [name, setName] = useState(initialName || t('flows.defaultFlowName'))
  const [description, setDescription] = useState(initialDescription || '')
  const [nameError, setNameError] = useState('')

  // Update state when modal opens with new initial values
  useEffect(() => {
    if (open) {
      setName(initialName || t('flows.defaultFlowName'))
      setDescription(initialDescription || '')
      setNameError('')
    }
  }, [open, initialName, initialDescription])

  useKeyboardShortcut({
    key: 's',
    ctrlOrCmd: true,
    callback: () => {
      handleSave()
    }
  })

  const handleSave = () => {
    if (!name.trim()) {
      setNameError(t('flows.flowNameRequired'))
      return
    }
    onSave(name, description)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('flows.saveFlowTitle')}</DialogTitle>
          <DialogDescription>
            {t('flows.saveFlowDescription')}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name" className="flex items-center justify-between">
              {t('flows.name')}
              {nameError && <span className="text-xs text-destructive">{nameError}</span>}
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                if (e.target.value.trim()) setNameError('')
              }}
              placeholder={t('flows.enterFlowName')}
              className={nameError ? 'border-destructive' : ''}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">{t('flows.description')}</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('flows.enterDescription')}
              className="resize-none"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('flows.cancel')}
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? t('flows.saving') : t('flows.saveFlow')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
