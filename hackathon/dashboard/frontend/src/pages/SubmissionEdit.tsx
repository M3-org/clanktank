import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { useNavigate, useParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { Button } from '../components/Button'
import { Card, CardHeader, CardContent } from '../components/Card'
import { useAuth } from '../contexts/AuthContext'
import ProtectedRoute from '../components/ProtectedRoute'

interface SchemaField {
  name: string
  label: string
  type: 'text' | 'url' | 'textarea' | 'select' | 'file'
  required: boolean
  placeholder?: string
  maxLength?: number
  options?: string[]
  accept?: string
  maxSize?: number
  helperText?: string
  pattern?: string
}

interface SubmissionInputs {
  [key: string]: any
}

export default function SubmissionEdit() {
  const { id } = useParams<{ id: string }>()
  const { authState } = useAuth()
  const navigate = useNavigate()
  const [schema, setSchema] = useState<SchemaField[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [submissionWindowOpen, setSubmissionWindowOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<SubmissionInputs>()

  // Load submission data and schema
  useEffect(() => {
    const loadSubmission = async () => {
      if (!id) return
      
      try {
        const [submission, schemaResponse] = await Promise.all([
          hackathonApi.getSubmission(id),
          hackathonApi.fetchSubmissionSchema()
        ])
        
        // Check submission window status
        setSubmissionWindowOpen(schemaResponse.submission_window_open)
        
        // Use all schema fields
        const schemaFields = schemaResponse.fields || []
        setSchema(schemaFields)

        // Pre-populate form with existing data
        const formData: any = {}
        
        // Populate all fields from submission
        schemaFields.forEach((field: SchemaField) => {
          formData[field.name] = (submission as any)[field.name] || ''
        })

        // Auto-populate Discord username if Discord authenticated
        if (authState.discordUser) {
          formData.discord_handle = authState.discordUser.username
        }

        reset(formData)
        
      } catch (err: any) {
        console.error('Failed to load submission:', err)
        setError('Failed to load submission data')
      } finally {
        setIsLoading(false)
      }
    }

    loadSubmission()
  }, [id, reset, authState.discordUser])

  const onSubmit = async (data: SubmissionInputs) => {
    if (!id) return
    
    try {
      setIsSubmitting(true)
      setError(null)
      
      // Ensure Discord username is populated
      if (!data.discord_handle && authState.discordUser) {
        data.discord_handle = authState.discordUser.username
      }
      
      // Handle file upload for project_image
      if (data.project_image) {
        if (data.project_image instanceof FileList) {
          const file = data.project_image[0]
          if (file) {
            try {
              const uploadResult = await hackathonApi.uploadImage(file, id)
              data.project_image = uploadResult.url
            } catch (uploadError) {
              console.error('Image upload failed:', uploadError)
              toast.error('Image upload failed. Submission will proceed without image.')
              data.project_image = ''
            }
          }
        } else if (typeof data.project_image === 'string') {
          // Keep existing URL
        } else {
          delete data.project_image
        }
      }
      
      // Submit the edit
      await hackathonApi.editSubmission(id, data)
      
      toast.success('Submission updated successfully!')
      navigate(`/submission/${id}`)
      
    } catch (error: any) {
      console.error('Edit submission error:', error)
      
      if (error.response?.status === 403) {
        setError('You can only edit submissions you created, or the submission window has closed')
      } else if (error.response?.status === 404) {
        setError('Submission not found')
      } else if (error.response?.status === 422) {
        // Handle validation errors
        const errorData = error.response.data
        if (errorData.detail && Array.isArray(errorData.detail)) {
          errorData.detail.forEach((validationError: any) => {
            const field = validationError.loc?.[validationError.loc.length - 1]
            const message = validationError.msg
            if (field) {
              toast.error(`${field}: ${message}`, { duration: 6000 })
            }
          })
        } else {
          setError('Please check your form inputs and try again.')
        }
      } else if (error.response?.status === 401) {
        setError('Authentication required. Please log in with Discord.')
      } else {
        setError('Failed to update submission. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!submissionWindowOpen) {
    return (
      <ProtectedRoute>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card className="max-w-lg mx-auto mt-16">
            <CardContent className="text-center py-12">
              <div className="rounded-full bg-red-100 h-16 w-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-2xl">⏰</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Editing Window Closed
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                The submission window has closed. Submissions can no longer be edited.
              </p>
              <Button 
                variant="secondary" 
                onClick={() => navigate(`/submission/${id}`)}
              >
                View Submission
              </Button>
            </CardContent>
          </Card>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Discord Authentication Status */}
        {authState.authMethod === 'discord' && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-green-600 dark:text-green-400 text-xl">✅</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                  Authenticated via Discord
                </h3>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Welcome {authState.discordUser?.username}! You can edit this submission.
                </p>
              </div>
            </div>
          </div>
        )}

        <Card>
          <CardHeader>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Edit Submission
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Update your hackathon project details
            </p>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {schema.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  
                  {field.type === 'textarea' ? (
                    <textarea
                      {...register(field.name, { 
                        required: field.required ? `${field.label} is required` : false,
                        maxLength: field.maxLength ? {
                          value: field.maxLength,
                          message: `Maximum ${field.maxLength} characters`
                        } : undefined,
                        pattern: field.pattern ? {
                          value: new RegExp(field.pattern),
                          message: `Please enter a valid ${field.label.toLowerCase()}`
                        } : undefined
                      })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                      rows={4}
                      readOnly={field.name === 'discord_handle' && authState.authMethod === 'discord'}
                    />
                  ) : field.type === 'select' ? (
                    <select
                      {...register(field.name, { 
                        required: field.required ? `${field.label} is required` : false 
                      })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                    >
                      <option value="">Select an option</option>
                      {field.options?.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : field.type === 'file' ? (
                    <input
                      type="file"
                      {...register(field.name, { 
                        required: false // Don't require file on edit
                      })}
                      accept={field.accept}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                    />
                  ) : (
                    <input
                      type={field.type === 'url' ? 'url' : 'text'}
                      {...register(field.name, { 
                        required: field.required ? `${field.label} is required` : false,
                        maxLength: field.maxLength ? {
                          value: field.maxLength,
                          message: `Maximum ${field.maxLength} characters`
                        } : undefined,
                        pattern: field.pattern ? {
                          value: new RegExp(field.pattern),
                          message: `Please enter a valid ${field.label.toLowerCase()}`
                        } : undefined
                      })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                      readOnly={field.name === 'discord_handle' && authState.authMethod === 'discord'}
                    />
                  )}
                  
                  {field.helperText && (
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {field.helperText}
                    </p>
                  )}
                  
                  {errors[field.name] && (
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                      {errors[field.name]?.message as string}
                    </p>
                  )}
                </div>
              ))}

              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1"
                >
                  {isSubmitting ? 'Updating...' : 'Update Submission'}
                </Button>
                
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => navigate(`/submission/${id}`)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
} 
