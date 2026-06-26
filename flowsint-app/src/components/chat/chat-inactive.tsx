import { Link } from '@tanstack/react-router'
import { KeyRound, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTranslation } from 'react-i18next'

export default function ChatInactive({ onClose }: { onClose: any }) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col h-full items-center justify-center relative py-16 px-4">
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 absolute top-3 right-3"
        onClick={onClose}
      >
        <X className="h-4 w-4" />
      </Button>
      <div className="w-14 h-14 mb-5 text-muted-foreground/30">
        <KeyRound className="w-full h-full" strokeWidth={1.5} />
      </div>
      <h3 className="text-sm font-medium text-foreground mb-1">{t('chat.apiKeyRequired')}</h3>
      <p className="text-sm text-muted-foreground text-center max-w-[260px] mb-5">
        {t('chat.apiKeyDescriptionBefore')}{' '}
        <code className="text-xs bg-muted px-1.5! py-0.5! rounded">MISTRAL_API_KEY</code>{' '}
        {t('chat.apiKeyDescriptionAfter')}
      </p>
      <Link to="/dashboard/vault">
        <Button size="sm" className="h-8 text-xs gap-1.5">
          {t('chat.goToVault')}
        </Button>
      </Link>
    </div>
  )
}
