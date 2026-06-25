// src/routes/register.tsx
import { createFileRoute, Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import { useRegister } from '@/hooks/use-auth'
import { useForm, FormProvider } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import FormField from '@/components/shared/form-field'
import { Button } from '@/components/ui/button'
import i18n from '@/i18n'

export const Route = createFileRoute('/register')({
  component: Register
})

const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, i18n.t('auth.usernameMin'))
      .max(50, i18n.t('auth.usernameMax')),
    email: z.string().email(i18n.t('auth.emailInvalid')),
    password: z.string().min(6, i18n.t('auth.passwordMin')),
    confirmPassword: z.string()
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: i18n.t('auth.passwordsMismatch'),
    path: ['confirmPassword']
  })

type RegisterFormValues = z.infer<typeof registerSchema>

function Register() {
  const { t } = useTranslation()
  const methods = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    }
  })

  const registerMutation = useRegister()

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      const { confirmPassword, ...registerData } = data
      await registerMutation.mutateAsync(registerData)
    } catch (error) {
      console.error("Erreur d'inscription:", error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold">{t('auth.registerTitle')}</h2>
        </div>

        <FormProvider {...methods}>
          <form className="mt-8 space-y-6" onSubmit={methods.handleSubmit(onSubmit)}>
            {registerMutation.error && (
              <div className="p-3 mb-4 text-sm bg-red-100 border border-red-400 text-red-700 rounded">
                {registerMutation.error instanceof Error
                  ? registerMutation.error.message
                  : t('auth.registerError')}
              </div>
            )}

            <div className="space-y-4">
              <FormField name="username" label={t('auth.username')} />
              <FormField name="email" label={t('auth.email')} type="email" />
              <FormField name="password" label={t('auth.password')} type="password" />
              <FormField name="confirmPassword" label={t('auth.confirmPassword')} type="password" />
            </div>

            <div>
              <Button
                type="submit"
                disabled={registerMutation.isPending || methods.formState.isSubmitting}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2"
              >
                {registerMutation.isPending || methods.formState.isSubmitting ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 
                           5.291A7.962 7.962 0 014 12H0c0 
                           3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    {t('auth.registering')}
                  </span>
                ) : (
                  t('auth.registerButton')
                )}
              </Button>
            </div>
          </form>
        </FormProvider>

        <div className="text-center mt-4">
          <p className="text-sm">
            {t('auth.haveAccount')}{' '}
            <Link to="/login" className="font-medium text-primary underline">
              {t('auth.login')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
