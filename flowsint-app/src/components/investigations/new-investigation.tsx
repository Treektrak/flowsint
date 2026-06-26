import { useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from '@tanstack/react-router'
import { toast } from 'sonner'
import { investigationService } from '@/api/investigation-service'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/api/query-keys'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import * as z from 'zod'

// Schema de validation Zod
const createInvestigationSchema = (t: (key: string) => string) =>
  z.object({
    name: z
      .string()
      .min(1, t('dialogs.validationNameRequired'))
      .min(3, t('dialogs.validationNameMin'))
      .max(100, t('dialogs.validationNameMax')),
    description: z.string().max(500, t('dialogs.validationDescriptionMax')).optional()
  })

type InvestigationFormData = z.infer<ReturnType<typeof createInvestigationSchema>>

interface NewInvestigationProps {
  children: ReactNode
  noDropDown?: boolean
}

export default function NewInvestigation({ children, noDropDown = false }: NewInvestigationProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const router = useRouter()
  const queryClient = useQueryClient()

  const form = useForm<InvestigationFormData>({
    resolver: zodResolver(createInvestigationSchema(t)),
    defaultValues: {
      name: '',
      description: ''
    }
  })

  const {
    handleSubmit,
    formState: { isSubmitting },
    reset
  } = form

  // Create investigation mutation
  const createInvestigationMutation = useMutation({
    mutationFn: investigationService.create,
    onSuccess: (result) => {
      if (result.id) {
        toast.success(t('dialogs.investigationCreated'))
        router.navigate({ to: `/dashboard/investigations/${result.id}` })
        // Invalidate investigations list
        queryClient.invalidateQueries({
          queryKey: queryKeys.investigations.list
        })
      } else {
        toast.error(result.error || t('dialogs.investigationCreateFailed'))
      }
    },
    onError: (error) => {
      toast.error(error.message)
    }
  })

  const onSubmit = async (data: InvestigationFormData) => {
    try {
      await createInvestigationMutation.mutateAsync(JSON.stringify(data))
    } catch (error) {
      console.error('Error creating investigation:', error)
    }
  }

  const handleClose = () => {
    setOpen(false)
    reset() // Reset du formulaire avec React Hook Form
  }

  const InvestigationForm = () => (
    <Form {...form}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid gap-4 py-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('dialogs.investigationName')}</FormLabel>
                <FormControl>
                  <Input
                    required
                    placeholder={t('dialogs.investigationNamePlaceholder')}
                    disabled={isSubmitting}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('dialogs.description')}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t('dialogs.investigationDescriptionPlaceholder')}
                    disabled={isSubmitting}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('dialogs.creating') : t('dialogs.createInvestigation')}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  )

  if (noDropDown) {
    return (
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <span role="button">{children}</span>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{t('dialogs.newInvestigation')}</DialogTitle>
            <DialogDescription>{t('dialogs.newInvestigationDescription')}</DialogDescription>
          </DialogHeader>
          <InvestigationForm />
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => setOpen(true)}>
            {t('dialogs.newInvestigation')}
            <span className="ml-auto text-xs text-muted-foreground">⌘ E</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{t('dialogs.newInvestigation')}</DialogTitle>
            <DialogDescription>{t('dialogs.newInvestigationDescription')}</DialogDescription>
          </DialogHeader>
          <InvestigationForm />
        </DialogContent>
      </Dialog>
    </>
  )
}
