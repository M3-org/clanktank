import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { Button } from '../components/Button'
import { Card, CardContent } from '../components/Card'
import { useAuth } from '../contexts/AuthContext'
import ProtectedRoute from '../components/ProtectedRoute'
import { Download, Upload } from 'lucide-react'
import { useRef } from 'react';

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
  const [searchParams, setSearchParams] = useSearchParams();
  const [schema, setSchema] = useState<SchemaField[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [submissionWindowOpen, setSubmissionWindowOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue
  } = useForm<SubmissionInputs>({
    mode: 'onChange' // Enable real-time validation and state tracking
  })

  // Real-time URL state management using React Hook Form's watch
  const watchedValues = watch();
  useEffect(() => {
    if (schema.length > 0 && watchedValues) {
      const timeoutId = setTimeout(() => {
        try {
          // Real-time URL updates for collaborative editing
          const cleanValues = Object.fromEntries(
            Object.entries(watchedValues).filter(([, value]) => 
              value !== null && 
              value !== undefined && 
              value !== '' && 
              !(typeof value === 'string' && value.trim() === '')
            )
          );
          
          // Only update URL if we have meaningful data or need to clear it
          const currentDraft = searchParams.get('draft');
          const hasCleanData = Object.keys(cleanValues).length > 0;
          
          if (hasCleanData) {
            const encodedState = encodeURIComponent(JSON.stringify(cleanValues));
            // Only update if the encoded state actually changed
            if (currentDraft !== encodedState) {
              setSearchParams({ draft: encodedState }, { replace: true });
            }
          } else if (currentDraft) {
            // Only clear URL if there was previously a draft parameter
            setSearchParams({}, { replace: true });
          }
        } catch (error) {
          console.error('Failed to update URL state:', error)
        }
      }, 1000)

      return () => clearTimeout(timeoutId)
    }
  }, [watchedValues, schema, setSearchParams, searchParams]);

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

        // Initialize form with proper defaultValues
        const defaultFormValues: any = {};
        
        // Start with existing submission data
        schemaFields.forEach((field: SchemaField) => {
          defaultFormValues[field.name] = (submission as any)[field.name] || '';
        });

        // Auto-populate Discord username if authenticated
        if (authState.discordUser) {
          defaultFormValues.discord_handle = authState.discordUser.username;
        }

        // Check for URL state override (for collaborative editing)
        const urlState = searchParams.get('draft');
        if (urlState) {
          try {
            const urlData = JSON.parse(decodeURIComponent(urlState));
            
            // Merge URL data with existing submission, preserving Discord username
            Object.keys(urlData).forEach(key => {
              if (key !== 'discord_handle' && schemaFields.some((f: SchemaField) => f.name === key)) {
                defaultFormValues[key] = urlData[key];
              }
            });
            
            toast.success('Form state loaded from URL!', { duration: 2000 });
          } catch (error) {
            console.error('Failed to restore from URL:', error);
          }
        }

        // Use React Hook Form's reset with proper defaultValues
        reset(defaultFormValues);
        
      } catch (err: any) {
        console.error('Failed to load submission:', err)
        setError('Failed to load submission data')
      } finally {
        setIsLoading(false)
      }
    }

    loadSubmission()
  }, [id, reset, authState.discordUser, searchParams])

  // If project_image is a URL, set preview
  useEffect(() => {
    if (schema.length && !isLoading) {
      const imageField = schema.find(f => f.name === 'project_image');
      if (imageField && typeof watch('project_image') === 'string' && watch('project_image')) {
        setImagePreview(watch('project_image'));
      }
    }
  }, [schema, isLoading, watch]);

  const onSubmit = async (data: SubmissionInputs) => {
    if (!id) return;
    try {
      setIsSubmitting(true);
      setError(null);
      if (!data.discord_handle && authState.discordUser) {
        data.discord_handle = authState.discordUser.username;
      }
      let imageFile: File | null = null;
      if (data.project_image && data.project_image instanceof File) {
        imageFile = data.project_image;
      }
      // Remove file from submission data and submit edit
      const editData = { ...data };
      delete editData.project_image;
      await hackathonApi.editSubmission(id, editData);
      if (imageFile) {
        try {
          const uploadResult = await hackathonApi.uploadImage(imageFile, id);
          await hackathonApi.editSubmission(id, {
            ...editData,
            project_image: uploadResult.url
          });
        } catch (uploadError) {
          console.error('Image upload failed:', uploadError);
          toast.error('Image upload failed. Submission will proceed without image.');
        }
      }
      toast.success('Submission updated successfully!');
      navigate(`/submission/${id}`);
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

  // JSON Download/Upload helpers
  function generateTemplate(schema: SchemaField[]) {
    const template: any = {}
    schema.forEach(field => {
      if (field.name === 'project_image') {
        template['project_image'] = 'https://your-api-domain.com/uploads/example-image.png' // Example: leave blank for new, or use image URL if already uploaded
      } else if (field.name !== 'discord_handle' && field.name !== 'category') {
        template[field.name] = field.type === 'file' ? '' : (field.placeholder || '')
      }
    })
    return template
  }

  function handleDownloadTemplate() {
    // Get current form values instead of generating template
    const currentValues = watchedValues || {};
    
    // If form is empty, generate template; otherwise download current state
    const dataToDownload = Object.keys(currentValues).length > 0 && 
      Object.values(currentValues).some(val => val && val.toString().trim() !== '')
      ? currentValues
      : generateTemplate(schema);
    
    const blob = new Blob([JSON.stringify(dataToDownload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = Object.keys(currentValues).length > 0 
      ? 'my_hackathon_submission.json'
      : 'hackathon_submission_template.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleUploadJson(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 100 * 1024) {
      toast.error('File too large (max 100KB)')
      return
    }
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string)
        // Get current form values and merge with uploaded data
        const currentValues = watchedValues || {};
        const mergedData = { ...currentValues };
        
        // Apply uploaded fields (only valid schema fields, except discord_handle)
        Object.keys(data).forEach(key => {
          if (schema.some(f => f.name === key && key !== 'discord_handle')) {
            mergedData[key] = data[key];
          }
        });
        
        // Preserve Discord username
        if (authState.discordUser) {
          mergedData.discord_handle = authState.discordUser.username;
        }
        
        // Use reset to properly update all form state
        reset(mergedData);
        
        toast.success('Form auto-filled from JSON!')
      } catch {
        toast.error('Invalid JSON file')
      }
    }
    reader.readAsText(file)
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
        <Card>
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-2 items-center">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 md:col-span-1">
                Edit Submission
              </h1>
              <div className="flex flex-col items-end md:col-span-1">
                <span className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  💡 Tip: Download your current form state as JSON to save or share.
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={handleDownloadTemplate}
                    type="button"
                    size="sm"
                    className="py-1 px-3 rounded-md bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white font-semibold shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 text-xs"
                  >
                    <Download className="mr-1" size={16} />
                    Download JSON
                  </Button>
                  <label className="relative inline-flex items-center text-xs py-1 px-3 rounded-md bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold shadow-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" style={{ willChange: 'transform' }}>
                    <Upload className="mr-1" size={16} />
                    Upload JSON
                    <input
                      type="file"
                      accept="application/json"
                      onChange={handleUploadJson}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                      tabIndex={-1}
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>
          <CardContent>
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Project Name first */}
              {schema.filter(f => f.name === 'project_name').map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type="text"
                    {...register(field.name, {
                      required: field.required ? `${field.label} is required` : false
                    })}
                    placeholder={field.placeholder}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                  />
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
              {/* Discord Handle and Category side by side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {schema.filter(f => f.name === 'discord_handle' || f.name === 'category').map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {field.type === 'select' ? (
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
                    ) : (
                      <input
                        type="text"
                        {...register(field.name, {
                          required: field.required ? `${field.label} is required` : false
                        })}
                        placeholder={field.placeholder}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                        readOnly={field.name === 'discord_handle' && authState.authMethod === 'discord'}
                      />
                    )}
                    {/* Helper text for Discord Handle */}
                    {field.name === 'discord_handle' && authState.authMethod === 'discord' && (
                      <p className="mt-1 text-sm text-green-600 dark:text-green-400">
                        Signed in via Discord
                      </p>
                    )}
                    {/* Other helper text */}
                    {field.helperText && field.name !== 'discord_handle' && (
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
              </div>
              {/* GitHub URL and Demo Video URL side by side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {schema.filter(f => f.name === 'github_url' || f.name === 'demo_video_url').map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <input
                      type={field.type === 'url' ? 'url' : 'text'}
                      {...register(field.name, {
                        required: field.required ? `${field.label} is required` : false
                      })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                    />
                    {field.helperText && (
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {field.helperText}
                      </p>
                    )}
                    {field.name === 'demo_video_url' && (
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        💡 Try catbox.moe, gyazo, or sharex for free hosting
                      </p>
                    )}
                    {errors[field.name] && (
                      <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                        {errors[field.name]?.message as string}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              {/* Render the rest of the fields vertically, except paired fields and project_image */}
              {schema.filter(f => f.name !== 'project_name' && f.name !== 'discord_handle' && f.name !== 'category' && f.name !== 'twitter_handle' && f.name !== 'solana_address' && f.name !== 'github_url' && f.name !== 'demo_video_url' && f.name !== 'project_image').map((field) => (
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
              {/* Project image drag-and-drop field (already handled above) */}
              {schema.filter(f => f.name === 'project_image').map((field) => {
                return (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <div
                      ref={dropRef}
                      className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md cursor-pointer bg-gray-50 dark:bg-gray-800 hover:border-indigo-500 transition relative"
                      onDragOver={e => { e.preventDefault(); dropRef.current?.classList.add('border-indigo-500'); }}
                      onDragLeave={e => { e.preventDefault(); dropRef.current?.classList.remove('border-indigo-500'); }}
                      onDrop={e => {
                        e.preventDefault();
                        dropRef.current?.classList.remove('border-indigo-500');
                        const file = e.dataTransfer.files[0];
                        if (file && file.type.startsWith('image/')) {
                          setValue('project_image', file);
                          const reader = new FileReader();
                          reader.onload = ev => setImagePreview(ev.target?.result as string);
                          reader.readAsDataURL(file);
                        }
                      }}
                      onClick={() => {
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = 'image/*';
                        input.onchange = (e: any) => {
                          const file = e.target.files[0];
                          if (file && file.type.startsWith('image/')) {
                            setValue('project_image', file);
                            const reader = new FileReader();
                            reader.onload = ev => setImagePreview(ev.target?.result as string);
                            reader.readAsDataURL(file);
                          }
                        };
                        input.click();
                      }}
                    >
                      {imagePreview ? (
                        <img src={imagePreview} alt="Preview" className="max-h-28 object-contain rounded" />
                      ) : (
                        <div className="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                          <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4a1 1 0 011-1h8a1 1 0 011 1v12m-4 4h-4a1 1 0 01-1-1v-4m0 0l4-4m0 0l4 4m-4-4v12" /></svg>
                          <span className="text-xs">Drag & drop or click to upload image</span>
                        </div>
                      )}
                    </div>
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
                );
              })}
              {/* Twitter handle and Solana address side by side at the bottom */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {schema.filter(f => f.name === 'twitter_handle' || f.name === 'solana_address').map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <input
                      type="text"
                      {...register(field.name, {
                        required: field.required ? `${field.label} is required` : false
                      })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-gray-100"
                    />
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
              </div>
              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-indigo-600 dark:bg-indigo-500 hover:bg-indigo-700 dark:hover:bg-indigo-400 border border-indigo-700 dark:border-indigo-400 text-white font-semibold rounded-md shadow focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
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