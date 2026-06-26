import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Plus, XIcon } from "lucide-react"
import { Select, SelectItem, SelectContent, SelectTrigger, SelectValue } from "@/components/ui/select"
import { memo, useState } from "react"
import { v4 as uuidv4 } from "uuid"
import type { RuleFilter, Filters, RuleKey, RuleOperator } from "@/types/filter"
import { useTranslation } from "react-i18next"

type RuleFiltersProps = {
  filters: Filters
  setFilters: (filters: Filters) => void
}

function RuleFilters({ filters, setFilters }: RuleFiltersProps) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState<Filters>(filters)

  const { rules } = draft

  const setDraftRules = (newRules: RuleFilter[]) => {
    setDraft(prev => ({ ...prev, rules: newRules }))
  }

  const addRule = () => {
    setDraftRules([
      ...rules,
      {
        id: uuidv4(),
        key: "label",
        operator: "is",
        matcher: ""
      }
    ])
  }

  const removeRule = (id: string) => {
    setDraftRules(rules.filter(r => r.id !== id))
  }

  const updateRule = (id: string, patch: Partial<Omit<RuleFilter, "id">>) => {
    setDraftRules(
      rules.map(r => (r.id === id ? { ...r, ...patch } : r))
    )
  }

  const applyChanges = () => {
    setFilters(draft)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="opacity-90 text-sm">{t('misc2.filterByRule')}</p>

        <div className="flex gap-2">
          <Button
            variant="outline"
            className="border-dashed h-7 text-xs"
            size="sm"
            onClick={addRule}
          >
            <Plus className="text-muted-foreground !h-3 !w-3" /> {t('misc2.newRule')}
          </Button>

          <Button
            disabled={rules.length === 0}
            variant="default"
            className="h-7 text-xs"
            size="sm"
            onClick={applyChanges}
          >
            {t('misc2.apply')}
          </Button>
        </div>
      </div>

      {rules.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          {t('misc2.startByAddingRule')}
        </p>
      ) : (
        <ul className="space-y-2">
          {rules.map(rule => (
            <RuleItem
              key={rule.id}
              rule={rule}
              onChange={patch => updateRule(rule.id, patch)}
              onRemove={() => removeRule(rule.id)}
            />
          ))}
        </ul>
      )}
    </div>
  )
}


type RuleItemProps = {
  rule: RuleFilter
  onChange: (patch: Partial<Omit<RuleFilter, "id">>) => void
  onRemove: () => void
}

const RuleItem = memo(({ rule, onChange, onRemove }: RuleItemProps) => {
  const { t } = useTranslation()
  return (
  <li>
    <div className="flex gap-2 justify-between">
      <KeyDropDown value={rule.key} onChange={(v) => onChange({ key: v })} />

      <OperatorDropDown value={rule.operator} onChange={(v) => onChange({ operator: v })} />

      <Input
        value={rule.matcher}
        onChange={e => onChange({ matcher: e.target.value })}
        className="h-7 grow w-1/3"
        placeholder={t('misc2.matcher')}
      />

      <Button
        onClick={onRemove}
        variant="ghost"
        size="icon"
        className="rounded-full h-7 w-7 hover:bg-muted"
      >
        <XIcon />
      </Button>
    </div>
  </li>
  )
})


const KEYS: RuleKey[] = ["label", "domain", "ip"]
const OPERATORS: RuleOperator[] = ["is", "not", "like", "startsWith", "endsWith"]

const KeyDropDown = memo(({ value, onChange }: { value: RuleKey, onChange: (v: RuleKey) => void }) => {
  const { t } = useTranslation()
  return (
  <Select value={value} onValueChange={onChange}>
    <SelectTrigger className="!h-7 w-1/3">
      <SelectValue placeholder={t('misc2.property')} />
    </SelectTrigger>
    <SelectContent>
      {KEYS.map(k => <SelectItem key={k} value={k}>{k}</SelectItem>)}
    </SelectContent>
  </Select>
  )
})

const OperatorDropDown = memo(({ value, onChange }: { value: RuleOperator, onChange: (v: RuleOperator) => void }) => (
  <Select value={value} onValueChange={onChange}>
    <SelectTrigger className="!h-7 grow w-1/3">
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {OPERATORS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
    </SelectContent>
  </Select>
))

export default RuleFilters
