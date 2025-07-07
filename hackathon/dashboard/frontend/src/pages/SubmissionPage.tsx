import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
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

export default function SubmissionPage() {
  const { authState } = useAuth()
  const navigate = useNavigate()
  const [schema, setSchema] = useState<SchemaField[]>([])
  const [schemaLoaded, setSchemaLoaded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submissionWindowOpen, setSubmissionWindowOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset
  } = useForm<SubmissionInputs>()

  // Load schema on component mount
  useEffect(() => {
    const loadSchema = async () => {
      try {
        const schemaResponse = await hackathonApi.fetchSubmissionSchema()
        setSubmissionWindowOpen(schemaResponse.submission_window_open)
        
        // Use all schema fields for Discord users
        const schemaFields = schemaResponse.fields || []
        setSchema(schemaFields)
        setSchemaLoaded(true)

        // Auto-populate Discord username
        if (authState.discordUser) {
          setValue('discord_handle', authState.discordUser.username)
        }
        
        // Load any saved draft
        const draftKey = 'submission_draft'
        const savedDraft = localStorage.getItem(draftKey)
        if (savedDraft) {
          try {
            const draft = JSON.parse(savedDraft)
            
                         // Populate form with saved data, but override Discord username
             Object.keys(draft).forEach(key => {
               if (key !== 'discord_handle') { // Don't override Discord username
                 setValue(key, draft[key])
               }
             })
            
            toast.success('Draft restored!', { duration: 2000 })
          } catch (error) {
            console.error('Failed to restore draft:', error)
          }
        }
        
      } catch (error) {
        console.error('Failed to load schema:', error)
        setError('Failed to load form schema')
      }
    }

    loadSchema()
  }, [setValue, authState.discordUser])

  // Auto-save draft
  const formData = watch()
  useEffect(() => {
    if (schemaLoaded && Object.keys(formData).length > 0) {
      const timeoutId = setTimeout(() => {
        try {
          localStorage.setItem('submission_draft', JSON.stringify(formData))
        } catch (error) {
          console.error('Failed to save draft:', error)
        }
      }, 1000)

      return () => clearTimeout(timeoutId)
    }
  }, [formData, schemaLoaded])

  const clearDraft = () => {
    localStorage.removeItem('submission_draft')
    reset()
    // Re-populate Discord username
    if (authState.discordUser) {
      setValue('discord_handle', authState.discordUser.username)
    }
  }

  const onSubmit = async (data: SubmissionInputs) => {
    if (!submissionWindowOpen) {
      setError('Submission window is closed')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)
      
      // Ensure Discord username is populated
      if (!data.discord_handle && authState.discordUser) {
        data.discord_handle = authState.discordUser.username
      }
      
      // Remove project_image from data if it's a FileList (we'll upload after submission)
      let file: File | undefined = undefined;
      if (data.project_image && data.project_image instanceof FileList) {
        file = data.project_image[0];
        delete data.project_image;
      }
      
      // 1. Create the submission (without image)
      const result = await hackathonApi.createSubmission(data);
      
      if (result.success && file) {
        try {
          // 2. Upload the image with the new submission_id
          const uploadResult = await hackathonApi.uploadImage(file, result.submission_id);
          // 3. Update the submission with the image URL
          await hackathonApi.editSubmission(result.submission_id, { project_image: uploadResult.url });
        } catch (uploadError) {
          console.error('Image upload failed:', uploadError);
          toast.error('Image upload failed. Submission will proceed without image.');
        }
      }
      
      if (result.success) {
        toast.success('Submission created successfully!');
        localStorage.removeItem('submission_draft');
        navigate(`/submission/${result.submission_id}`);
      } else {
        setError(result.error || 'Submission failed');
      }
    } catch (error: any) {
      console.error('Submission error:', error);
      
      if (error.response?.status === 422) {
        const errorData = error.response.data;
        if (errorData.detail && Array.isArray(errorData.detail)) {
          errorData.detail.forEach((validationError: any) => {
            const field = validationError.loc?.[validationError.loc.length - 1];
            const message = validationError.msg;
            if (field) {
              toast.error(`${field}: ${message}`, { duration: 6000 });
            }
          });
        } else {
          setError('Please check your form inputs and try again.');
        }
      } else if (error.response?.status === 401) {
        setError('Authentication required. Please log in with Discord.');
      } else {
        setError('Failed to submit. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!schemaLoaded) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
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
                Submission Window Closed
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                The submission window for this hackathon has ended. No new submissions are being accepted.
              </p>
              <Button 
                variant="secondary" 
                onClick={() => navigate('/dashboard')}
              >
                View Submissions
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
                  Welcome {authState.discordUser?.username}! Your Discord username will be auto-populated.
                </p>
              </div>
            </div>
          </div>
        )}

        <Card>
          <CardHeader>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Submit Your Project
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Share your hackathon project with the community
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
                        required: field.required ? `${field.label} is required` : false 
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
                  {isSubmitting ? 'Submitting...' : 'Submit Project'}
                </Button>
                
                <Button
                  type="button"
                  variant="ghost"
                  onClick={clearDraft}
                  disabled={isSubmitting}
                >
                  Clear Form
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
} 