import { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { Button } from '../components/Button'
import { Card, CardContent } from '../components/Card'
import { useAuth } from '../contexts/AuthContext'
import ProtectedRoute from '../components/ProtectedRoute'
import { Download, Upload } from 'lucide-react'
import { SubmissionDetail } from '../types';

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
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [schema, setSchema] = useState<SchemaField[]>([])
  const [schemaLoaded, setSchemaLoaded] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submissionWindowOpen, setSubmissionWindowOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [draftAlreadyRestored, setDraftAlreadyRestored] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset
  } = useForm<SubmissionInputs>({
    mode: 'onChange' // Enable real-time validation and state tracking
  })

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
        
        // Initialize form with proper defaultValues from URL or localStorage
        if (!draftAlreadyRestored) {
          const defaultFormValues: any = {};
          
          // Set Discord username first
          if (authState.discordUser) {
            defaultFormValues.discord_handle = authState.discordUser.username;
          }
          
          // Try URL state first (for collaborative sharing)
          const urlState = searchParams.get('draft');
          if (urlState) {
            try {
              const urlData = JSON.parse(decodeURIComponent(urlState));
              
              // Merge URL data, preserving Discord username
              Object.keys(urlData).forEach(key => {
                if (key !== 'discord_handle') {
                  defaultFormValues[key] = urlData[key];
                }
              });
              
              // Use React Hook Form's reset with new defaultValues
              reset(defaultFormValues);
              toast.success('Form state loaded from URL!', { duration: 2000 });
              setDraftAlreadyRestored(true);
              return;
            } catch (error) {
              console.error('Failed to restore from URL:', error);
            }
          }
          
          // Fall back to localStorage
          const savedDraft = localStorage.getItem('submission_draft');
          if (savedDraft) {
            try {
              const draftData = JSON.parse(savedDraft);
              
              // Merge localStorage data, preserving Discord username
              Object.keys(draftData).forEach(key => {
                if (key !== 'discord_handle') {
                  defaultFormValues[key] = draftData[key];
                }
              });
              
              // Use React Hook Form's reset with new defaultValues
              reset(defaultFormValues);
              toast.success('Draft restored!', { duration: 2000 });
            } catch (error) {
              console.error('Failed to restore draft:', error);
            }
          } else {
            // Just set Discord username if no draft data
            reset(defaultFormValues);
          }
          
          setDraftAlreadyRestored(true);
        }
        
      } catch (error) {
        console.error('Failed to load schema:', error)
        setError('Failed to load form schema')
      }
    }

    loadSchema()
  }, [setValue, authState.discordUser, searchParams, reset, draftAlreadyRestored])

  // Real-time URL state management using React Hook Form's watch
  const watchedValues = watch();
  useEffect(() => {
    if (schemaLoaded && watchedValues) {
      const timeoutId = setTimeout(() => {
        try {
          // Save to localStorage (existing functionality)
          if (Object.keys(watchedValues).length > 0) {
            localStorage.setItem('submission_draft', JSON.stringify(watchedValues))
          }
          
          // Real-time URL updates for collaborative sharing
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
          console.error('Failed to save draft:', error)
        }
      }, 1000)

      return () => clearTimeout(timeoutId)
    }
  }, [watchedValues, schemaLoaded, setSearchParams, searchParams])

  useEffect(() => {
    if (id) {
      hackathonApi.getSubmission(id).then(setSubmission).catch(() => setSubmission(null));
    }
  }, [id]);

  const clearDraft = () => {
    localStorage.removeItem('submission_draft');
    
    // Clear URL state
    setSearchParams({}, { replace: true });
    
    // Reset form to initial state with only Discord username
    const cleanDefaults = authState.discordUser 
      ? { discord_handle: authState.discordUser.username }
      : {};
    
    reset(cleanDefaults);
    setDraftAlreadyRestored(true);
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
      
      // Store file for later upload (after submission creation)
      let imageFile: File | null = null
      if (data.project_image && data.project_image instanceof File) {
        imageFile = data.project_image
      }
      
      // Remove file from submission data and create submission first
      const submissionData = { ...data }
      delete submissionData.project_image
      
      const result = await hackathonApi.createSubmission(submissionData)
      
      // If submission successful and we have an image, upload it
      if (result.success && imageFile) {
        try {
          const uploadResult = await hackathonApi.uploadImage(imageFile, result.submission_id)
          
          // Update submission with image URL
          await hackathonApi.editSubmission(result.submission_id, {
            ...submissionData,
            project_image: uploadResult.url
          })
        } catch (uploadError) {
          console.error('Image upload failed:', uploadError)
          toast.error('Submission created but image upload failed. You can edit and add the image later.')
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

  // JSON Download/Upload helpers
  function generateTemplate(schema: SchemaField[]) {
    const template: any = {}
    schema.forEach(field => {
      if (field.name === 'project_image') {
        template['project_image'] = 'https://your-api-domain.com/uploads/example-image.png' // Example: leave blank for new, or use image URL if already uploaded
      } else if (field.name !== 'discord_handle' && field.name !== 'category') {
        if (field.type === 'select' && field.options) {
          template[field.name] = field.options[0]
        } else {
          template[field.name] = field.type === 'file' ? '' : (field.placeholder || '')
        }
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
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 100 * 1024) {
      toast.error('File too large (max 100KB)');
      e.target.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        const validFields = schema
          .map(f => f.name)
          .filter(name => name !== 'discord_handle');
        const unknownFields = Object.keys(data).filter(key => !validFields.includes(key));
        const appliedFields = Object.keys(data).filter(key => validFields.includes(key));
        if (appliedFields.length === 0) {
          toast.error('No valid fields found in uploaded JSON.');
        } else {
          // Get current form values and merge with uploaded data
          const currentValues = watchedValues || {};
          const mergedData = { ...currentValues };
          
          // Apply uploaded fields
          appliedFields.forEach(key => {
            mergedData[key] = data[key];
          });
          
          // Preserve Discord username
          if (authState.discordUser) {
            mergedData.discord_handle = authState.discordUser.username;
          }
          
          // Use reset to properly update all form state
          reset(mergedData);
          
          toast.success(`Form auto-filled from JSON!${unknownFields.length ? ` Ignored: ${unknownFields.join(', ')}` : ''}`);
        }
        if (unknownFields.length > 0) {
          toast(
            `Ignored unknown fields: ${unknownFields.join(', ')}`,
            { icon: '⚠️', duration: 6000 }
          );
        }
      } catch (err) {
        toast.error('Invalid JSON file');
      }
      e.target.value = '';
    };
    reader.readAsText(file);
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
        <Card>
          {submission && (
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {submission.project_name}
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
                  <Button
                    onClick={clearDraft}
                    type="button"
                    size="sm"
                    className="py-1 px-3 rounded-md bg-white dark:bg-gray-900 border border-indigo-200 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300 font-semibold shadow-sm hover:bg-indigo-50 dark:hover:bg-gray-800 transition"
                  >
                    Clear Form
                  </Button>
                </div>
              </div>
            </div>
          )}
          {/* JSON Draft Utility UI Block */}
          {schemaLoaded && submissionWindowOpen && (
            <>
              <div className="flex items-center justify-between mb-6 p-3 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg">
                <div className="flex items-center">
                  <span className="text-blue-600 dark:text-blue-400 text-xl mr-2">📝</span>
                  <span className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                    Save/Load your form state for faster filling.
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleDownloadTemplate}
                    type="button"
                    size="sm"
                    className="py-1 px-3 rounded-md bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white font-semibold shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 text-xs"
                  >
                    <Download className="mr-1" size={16}/> Download JSON
                  </Button>
                  <label className="relative inline-flex items-center text-xs py-1 px-3 rounded-md bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white font-semibold shadow-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" style={{ willChange: 'transform' }}>
                    <Upload className="mr-1" size={16}/> Upload JSON
                    <input
                      type="file"
                      accept="application/json"
                      onChange={handleUploadJson}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                      tabIndex={-1}
                    />
                  </label>
                  <Button
                    onClick={clearDraft}
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="py-1 px-3 rounded-md border border-blue-300 dark:border-blue-600 text-blue-700 dark:text-blue-200 bg-white dark:bg-blue-950 hover:bg-blue-50 dark:hover:bg-blue-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 text-xs"
                  >
                    Clear Draft
                  </Button>
                </div>
              </div>
            </>
          )}
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
              {/* Render the rest of the fields vertically, except paired fields */}
              {schema.filter(f => f.name !== 'project_name' && f.name !== 'discord_handle' && f.name !== 'category' && f.name !== 'twitter_handle' && f.name !== 'solana_address' && f.name !== 'github_url' && f.name !== 'demo_video_url').map((field) => {
                if (field.name === 'project_image') {
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
                }
                return (
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
                  {isSubmitting ? 'Submitting...' : 'Submit Project'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
}