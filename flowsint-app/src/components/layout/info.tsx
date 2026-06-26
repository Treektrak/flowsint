import { memo } from 'react'
import { HelpCircle } from 'lucide-react'
import { Dialog, DialogContent, DialogTrigger } from '../ui/dialog'
import { Button } from '../ui/button'
import { Trans, useTranslation } from 'react-i18next'

const InfoDialog = () => {
  const { t } = useTranslation()
  return (
    <>
      <Dialog>
        <DialogTrigger asChild>
          <div>
            <Button variant="ghost" size="sm" className="h-6 gap-1 text-xs">
              <HelpCircle className="h-3 w-3 opacity-60" />
            </Button>
          </div>
        </DialogTrigger>
        <DialogContent className="sm:max-w-2xl">
          <div className="p-2">
            <div className="p-2 text-sm space-y-4 overflow-y-auto max-h-[80vh]">
              <h2 className="text-base font-semibold flex items-center gap-2">
                {t('misc.aboutTraceon')}
              </h2>
              <p>
                <Trans i18nKey="misc.aboutIntro1" components={{ b: <strong /> }} />
              </p>

              <p>
                <Trans i18nKey="misc.aboutIntro2" components={{ b: <strong /> }} />
              </p>

              <h3 className="font-semibold">{t('misc.whatTraceonDoes')}</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>
                  <Trans i18nKey="misc.doesItem1" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.doesItem2" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.doesItem3" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.doesItem4" components={{ b: <strong /> }} />
                </li>
              </ul>

              <h3 className="font-semibold">{t('misc.whyUseTraceon')}</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>
                  <Trans i18nKey="misc.whyItem1" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.whyItem2" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.whyItem3" components={{ b: <strong /> }} />
                </li>
              </ul>

              <h3 className="font-semibold">{t('misc.useCases')}</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>
                  <Trans i18nKey="misc.useCase1" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.useCase2" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.useCase3" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.useCase4" components={{ b: <strong /> }} />
                </li>
                <li>
                  <Trans i18nKey="misc.useCase5" components={{ b: <strong /> }} />
                </li>
              </ul>

              <p>
                <Trans i18nKey="misc.aboutOutro" components={{ b: <strong /> }} />
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default memo(InfoDialog)
