import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Sparkles, Radar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { aiImport, spiderfootScan } from '@/api/agent-service'

interface AiToolsProps {
  sketchId?: string
  onDone?: () => void
}

export function AiTools({ sketchId, onDone }: AiToolsProps) {
  const { t } = useTranslation()
  const [importOpen, setImportOpen] = useState(false)
  const [scanOpen, setScanOpen] = useState(false)
  const [text, setText] = useState('')
  const [target, setTarget] = useState('')
  const [busy, setBusy] = useState(false)
  const [kind, setKind] = useState<'text' | 'logs'>('text')

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => setText(String(reader.result || ''))
    reader.readAsText(f)
    // эвристика: журналы логов
    if (/\.(log|evtx|csv|xml|syslog)$/i.test(f.name) || /security|system|application|auth/i.test(f.name)) {
      setKind('logs')
    }
  }

  const runImport = async () => {
    if (!sketchId || !text.trim()) return
    setBusy(true)
    const p = toast.loading(t('aiTools.importRunning'))
    try {
      const r = await aiImport(sketchId, text, kind)
      toast.success(t('aiTools.importDone', { nodes: r.nodes_added, edges: r.edges_added }), { id: p })
      setImportOpen(false)
      setText('')
      onDone?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : t('aiTools.failed'), { id: p })
    } finally {
      setBusy(false)
    }
  }

  const runScan = async () => {
    if (!sketchId || !target.trim()) return
    setBusy(true)
    const p = toast.loading(t('aiTools.scanRunning'))
    try {
      const r = await spiderfootScan(sketchId, target.trim())
      toast.success(t('aiTools.scanDone', { nodes: r.nodes_added, events: r.events ?? 0 }), { id: p })
      setScanOpen(false)
      setTarget('')
      onDone?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : t('aiTools.failed'), { id: p })
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      {/* ИИ-импорт из текста */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <Tooltip>
          <TooltipTrigger asChild>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 shadow-none" disabled={!sketchId}>
                <Sparkles className="h-4 w-4 opacity-70" />
              </Button>
            </DialogTrigger>
          </TooltipTrigger>
          <TooltipContent>{t('aiTools.import')}</TooltipContent>
        </Tooltip>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('aiTools.importTitle')}</DialogTitle>
            <DialogDescription>{t('aiTools.importDesc')}</DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="inline-flex rounded-md border border-border overflow-hidden text-xs">
              <button
                type="button"
                onClick={() => setKind('text')}
                className={kind === 'text' ? 'px-3 py-1 bg-primary text-primary-foreground' : 'px-3 py-1'}
              >
                {t('aiTools.modeText')}
              </button>
              <button
                type="button"
                onClick={() => setKind('logs')}
                className={kind === 'logs' ? 'px-3 py-1 bg-primary text-primary-foreground' : 'px-3 py-1'}
              >
                {t('aiTools.modeLogs')}
              </button>
            </div>
            <label className="text-xs text-primary cursor-pointer hover:underline">
              {t('aiTools.uploadFile')}
              <input
                type="file"
                accept=".txt,.log,.csv,.xml,.json,.evtx,.syslog"
                className="hidden"
                onChange={onFile}
              />
            </label>
          </div>
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={kind === 'logs' ? t('aiTools.logsPlaceholder') : t('aiTools.importPlaceholder')}
            className="min-h-[180px] font-mono text-xs"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportOpen(false)} disabled={busy}>
              {t('common.cancel')}
            </Button>
            <Button onClick={runImport} disabled={busy || !text.trim()}>
              <Sparkles className="h-4 w-4 mr-1.5" />
              {busy ? t('aiTools.importRunning') : t('aiTools.importRun')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SpiderFoot-скан */}
      <Dialog open={scanOpen} onOpenChange={setScanOpen}>
        <Tooltip>
          <TooltipTrigger asChild>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 shadow-none" disabled={!sketchId}>
                <Radar className="h-4 w-4 opacity-70" />
              </Button>
            </DialogTrigger>
          </TooltipTrigger>
          <TooltipContent>{t('aiTools.scan')}</TooltipContent>
        </Tooltip>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('aiTools.scanTitle')}</DialogTitle>
            <DialogDescription>{t('aiTools.scanDesc')}</DialogDescription>
          </DialogHeader>
          <Input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={t('aiTools.scanPlaceholder')}
            onKeyDown={(e) => e.key === 'Enter' && runScan()}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setScanOpen(false)} disabled={busy}>
              {t('common.cancel')}
            </Button>
            <Button onClick={runScan} disabled={busy || !target.trim()}>
              <Radar className="h-4 w-4 mr-1.5" />
              {busy ? t('aiTools.scanRunning') : t('aiTools.scanRun')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
