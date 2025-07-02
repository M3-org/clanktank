import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import { SubmissionInputs, SubmissionField } from '../types/submission';
import { postSubmission } from '../lib/api';
import { Button } from '../components/Button';
import { Card, CardHeader, CardContent } from '../components/Card';
import { loadSubmissionSchema, createYupSchemaFromFields } from '../lib/schemaLoader';

// Auto-save constants
const AUTO_SAVE_KEY = 'hackathon_submission_draft';
const AUTO_SAVE_INTERVAL = 30000; // 30 seconds - less aggressive
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY = 2000; // 2 seconds

const SubmissionPage: React.FC = () => {
    const navigate = useNavigate();
    const [schema, setSchema] = useState<SubmissionField[]>([]);
    const [schemaError, setSchemaError] = useState<string | null>(null);
    const [validationSchema, setValidationSchema] = useState<any>(null);
    const [schemaLoaded, setSchemaLoaded] = useState(false);
    const [schemaSource, setSchemaSource] = useState<'api' | 'cache' | 'fallback'>('fallback');
    const [retryAttempt, setRetryAttempt] = useState(0);
    const [lastAutoSave, setLastAutoSave] = useState<Date | null>(null);
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();
    
    const { 
        register, 
        control, 
        handleSubmit, 
        formState: { errors, isSubmitting },
        reset,
        watch,
        getValues,
        setValue
    } = useForm<SubmissionInputs>({ 
        resolver: validationSchema ? yupResolver(validationSchema) as any : undefined,
        defaultValues: Object.fromEntries(schema.map(f => [f.name, ''])) as any
    });

    // Watch all form values for auto-save
    const watchedValues = watch();

    // Load schema on mount
    useEffect(() => {
        const initializeSchema = async () => {
            try {
                const result = await loadSubmissionSchema('v2');
                setSchema(result.schema);
                setSchemaSource(result.source);
                
                if (result.error) {
                    setSchemaError(`Schema loaded from ${result.source}: ${result.error}`);
                } else {
                    setSchemaError(result.source === 'fallback' 
                        ? 'Using fallback schema (API unavailable)' 
                        : null
                    );
                }

                // Generate validation schema from loaded fields
                const yupSchema = await createYupSchemaFromFields(result.schema);
                setValidationSchema(yupSchema);
                setSchemaLoaded(true);
                
                // After schema is loaded, try to restore from auto-save
                restoreFromAutoSave(result.schema);
                
            } catch (error) {
                console.error('Failed to initialize schema:', error);
                setSchemaError('Failed to load schema, using minimal fallback');
                // Use a minimal fallback if everything fails
                const fallbackSchema: SubmissionField[] = [
                    { name: 'project_name', label: 'Project Name', type: 'text', required: true, placeholder: 'My Awesome Project' },
                    { name: 'team_name', label: 'Team Name', type: 'text', required: true, placeholder: 'The A-Team' },
                    { name: 'description', label: 'Project Description', type: 'textarea', required: true, placeholder: 'Describe your project' },
                ];
                setSchema(fallbackSchema);
                setSchemaSource('fallback');
                
                // Create a basic validation schema for fallback
                const fallbackYupSchema = await createYupSchemaFromFields(fallbackSchema);
                setValidationSchema(fallbackYupSchema);
                setSchemaLoaded(true);
                
                restoreFromAutoSave(fallbackSchema);
            }
        };
        
        initializeSchema();
    }, []);

    // Auto-save functionality
    const saveToLocalStorage = useCallback((data: Partial<SubmissionInputs>) => {
        try {
            // Create a clean copy excluding File objects for localStorage
            const cleanData = { ...data };
            Object.keys(cleanData).forEach(key => {
                if (cleanData[key] instanceof File) {
                    delete cleanData[key];
                }
            });
            
            const saveData = {
                formData: cleanData,
                timestamp: new Date().toISOString(),
                schemaSource
            };
            localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify(saveData));
            setLastAutoSave(new Date());
            setHasUnsavedChanges(false);
        } catch (error) {
            console.warn('Failed to auto-save form data:', error);
        }
    }, [schemaSource]);

    const restoreFromAutoSave = useCallback((currentSchema: SubmissionField[]) => {
        try {
            const saved = localStorage.getItem(AUTO_SAVE_KEY);
            if (saved) {
                const { formData, timestamp } = JSON.parse(saved);
                const saveDate = new Date(timestamp);
                const hoursSinceAuto = (Date.now() - saveDate.getTime()) / (1000 * 60 * 60);
                
                // Only restore if saved within last 24 hours
                if (hoursSinceAuto < 24) {
                    // Only restore fields that exist in current schema
                    const validFields = currentSchema.map(f => f.name);
                    const filteredData = Object.fromEntries(
                        Object.entries(formData).filter(([key]) => validFields.includes(key))
                    );
                    
                    // Set form values
                    Object.entries(filteredData).forEach(([key, value]) => {
                        if (value && typeof value === 'string') {
                            setValue(key as any, value);
                        }
                    });
                    
                    setLastAutoSave(saveDate);
                    toast.success(`Restored draft from ${saveDate.toLocaleString()}`, {
                        duration: 4000
                    });
                }
            }
        } catch (error) {
            console.warn('Failed to restore auto-save data:', error);
        }
    }, [setValue]);

    const clearAutoSave = useCallback(() => {
        localStorage.removeItem(AUTO_SAVE_KEY);
        setLastAutoSave(null);
        setHasUnsavedChanges(false);
        toast.success('Draft cleared');
    }, []);

    // Auto-save on form changes
    useEffect(() => {
        if (autoSaveTimeoutRef.current) {
            clearTimeout(autoSaveTimeoutRef.current);
        }

        autoSaveTimeoutRef.current = setTimeout(() => {
            const currentValues = getValues();
            const hasContent = Object.values(currentValues).some(value => {
                if (value instanceof File) return true;
                return value && typeof value === 'string' && value.trim() !== '';
            });
            
            if (hasContent) {
                saveToLocalStorage(currentValues);
            }
        }, AUTO_SAVE_INTERVAL);

        setHasUnsavedChanges(true);

        return () => {
            if (autoSaveTimeoutRef.current) {
                clearTimeout(autoSaveTimeoutRef.current);
            }
        };
    }, [watchedValues, getValues, saveToLocalStorage]);

    // Warn user about unsaved changes
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [hasUnsavedChanges]);

    // Download submission as JSON backup
    const downloadSubmissionBackup = useCallback(() => {
        const currentValues = getValues();
        const backupData = {
            formData: currentValues,
            timestamp: new Date().toISOString(),
            schema: schema,
            schemaSource,
            metadata: {
                userAgent: navigator.userAgent,
                url: window.location.href
            }
        };

        const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hackathon-submission-backup-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast.success('Submission backup downloaded');
    }, [getValues, schema, schemaSource]);



    // Retry submission with exponential backoff
    const submitWithRetry = async (data: SubmissionInputs, attempt: number = 1): Promise<any> => {
        try {
            const response = await postSubmission(data);
            setRetryAttempt(0);
            return response;
        } catch (error: any) {
            console.error(`Submission attempt ${attempt} failed:`, error);
            
            if (attempt < MAX_RETRY_ATTEMPTS && error.code !== 'ERR_NETWORK') {
                setRetryAttempt(attempt);
                toast.error(`Submission failed. Retrying... (${attempt}/${MAX_RETRY_ATTEMPTS})`);
                
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * Math.pow(2, attempt - 1)));
                return submitWithRetry(data, attempt + 1);
            }
            
            throw error;
        }
    };

    const onSubmit = async (data: SubmissionInputs) => {
        // Save final backup before submission
        saveToLocalStorage(data);
        
        try {
            // Handle file upload if present
            let submissionData = { ...data };
            
            if (data.project_image && data.project_image instanceof File) {
                toast.loading('Uploading image...', { duration: 2000 });
                
                const formData = new FormData();
                formData.append('file', data.project_image);
                
                const uploadResponse = await fetch('/api/upload-image', {
                    method: 'POST',
                    body: formData,
                });
                
                if (uploadResponse.ok) {
                    const uploadResult = await uploadResponse.json();
                    console.log('Image uploaded:', uploadResult.url);
                    // Set the uploaded image URL in the database field
                    submissionData.project_image = uploadResult.url;
                    toast.success('Image uploaded successfully!');
                } else {
                    const errorText = await uploadResponse.text();
                    console.error('Image upload failed:', errorText);
                    throw new Error(`Failed to upload image: ${uploadResponse.status} ${errorText}`);
                }
            } else if (data.project_image) {
                // Check what type of value we have
                if (typeof data.project_image === 'string') {
                    if (data.project_image.startsWith('/api/uploads/')) {
                        // Already a valid URL, keep it
                        console.log('Using existing image URL:', data.project_image);
                    } else {
                        // Invalid string value (not a valid upload URL) - remove it
                        console.warn('Invalid project_image string value detected, removing from submission:', data.project_image);
                        delete submissionData.project_image;
                    }
                } else {
                    // Not a File object and not a string - invalid value, remove it
                    console.warn('Invalid project_image value detected (not File or string), removing from submission:', data.project_image);
                    delete submissionData.project_image;
                }
                // If it's a File object, we should have handled it in the first condition, but it didn't match
                // This means there's a bug in our File detection logic
            } else {
                // No image selected or project_image is null/undefined - explicitly set to null
                console.log('No image selected, setting project_image to null');
                submissionData.project_image = null;
            }
            
            // Remove legacy image_url field if it exists
            delete submissionData.image_url;
            
            // Final safety check: ensure no File objects or invalid values are in submission data
            Object.keys(submissionData).forEach(key => {
                const value = submissionData[key];
                if (value instanceof File) {
                    console.error(`ERROR: File object found in submission data for field ${key}! Removing to prevent [object File] in database.`);
                    delete submissionData[key];
                } else if (typeof value === 'object' && value !== null && !(value as any instanceof Date)) {
                    console.error(`ERROR: Object found in submission data for field ${key}! Removing to prevent [object Object] in database.`);
                    delete submissionData[key];
                }
            });
            
            console.log('Final submission data project_image:', submissionData.project_image);
            
            const response = await submitWithRetry(submissionData);
            console.log('Submission response:', response);
            
            if (response.submission_id) {
                // Clear auto-save on successful submission
                clearAutoSave();
                
                toast.success(`Submission successful! Your submission ID is: ${response.submission_id}`, {
                    duration: 8000
                });
                // Copy ID to clipboard
                navigator.clipboard.writeText(response.submission_id).catch(() => {});
                
                reset();
                navigate(`/submission/${response.submission_id}`, { replace: true });
            } else {
                toast.success('Submission successful! Check the dashboard for your entry.');
                clearAutoSave();
                reset();
                navigate('/', { replace: true });
            }
        } catch (error: any) {
            console.error('Submission error:', error);
            
            // Save error details for debugging
            const errorBackup = {
                formData: data,
                error: {
                    message: error.message,
                    status: error.response?.status,
                    data: error.response?.data
                },
                timestamp: new Date().toISOString()
            };
            localStorage.setItem(`${AUTO_SAVE_KEY}_error`, JSON.stringify(errorBackup));
            
            if (error.response?.status === 429) {
                toast.error("Slow down, you're submitting too fast. Please try again in a moment.", {
                    duration: 6000
                });
            } else if (error.response?.status === 422) {
                // Handle Pydantic validation errors
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
                    toast.error('Please check your form inputs and try again.', { duration: 6000 });
                }
            } else if (error.code === 'ERR_NETWORK') {
                toast.error('Network error. Please check your connection and try again.', {
                    duration: 8000
                });
            } else {
                toast.error('An error occurred while submitting. Your work has been saved locally.', {
                    duration: 8000
                });
            }
        }
    };

    return (
        <div className="p-4 md:p-10">
            <Toaster position="top-right" />
            <Card className="max-w-4xl mx-auto">
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Submit Your Hackathon Project</h1>
                            <p className="mt-2 text-gray-600">
                                Fill out the details below to enter your project into the Clank Tank Hackathon. 
                                All fields with an * are required.
                            </p>
                            {schemaError && (
                                <p className="text-yellow-600 text-sm mt-2">{schemaError}</p>
                            )}
                            {lastAutoSave && (
                                <p className="text-green-600 text-xs mt-1">
                                    💾 Last saved: {lastAutoSave.toLocaleTimeString()}
                                </p>
                            )}
                            {retryAttempt > 0 && (
                                <p className="text-blue-600 text-xs mt-1">
                                    🔄 Retry attempt: {retryAttempt}/{MAX_RETRY_ATTEMPTS}
                                </p>
                            )}
                        </div>
                        {lastAutoSave && (
                            <div className="flex gap-2">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearAutoSave}
                                    className="text-xs text-gray-500 hover:text-red-600"
                                >
                                    🗑️ Clear Draft
                                </Button>
                            </div>
                        )}
                    </div>
                </CardHeader>
                <CardContent>
                    {!schemaLoaded ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                                <p className="text-gray-600">Loading submission form...</p>
                                {schemaError && (
                                    <p className="text-yellow-600 text-sm mt-2">{schemaError}</p>
                                )}
                            </div>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                        {/* Render fields dynamically from schema */}
                        {schema.map(field => (
                            <div key={field.name} className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {field.label}{field.required ? ' *' : ''}
                                </label>
                                {field.type === 'text' && (
                                    <input
                                        {...register(field.name as any)}
                                        type="text"
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'url' && (
                                    <input
                                        {...register(field.name as any)}
                                        type="url"
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'textarea' && (
                                    <textarea
                                        {...register(field.name as any)}
                                        rows={field.maxLength && field.maxLength > 500 ? 4 : 3}
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'select' && Array.isArray(field.options) && (
                                    <Controller
                                        control={control}
                                        name={field.name as any}
                                        render={({ field: ctrlField }) => (
                                            <select
                                                {...ctrlField}
                                                value={typeof ctrlField.value === 'string' ? ctrlField.value : ''}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                            >
                                                <option value="">{field.placeholder || 'Select an option'}</option>
                                                {(field.options ?? []).map(option => (
                                                    <option key={option} value={option}>{option}</option>
                                                ))}
                                            </select>
                                        )}
                                    />
                                )}
                                {field.type === 'file' && (
                                    <Controller
                                        control={control}
                                        name={field.name as any}
                                        render={({ field: ctrlField }) => (
                                            <div className="space-y-2">
                                                <input
                                                    type="file"
                                                    accept={field.accept}
                                                    onChange={(e) => {
                                                        const file = e.target.files?.[0];
                                                        if (file) {
                                                            // Validate file size
                                                            if (field.maxSize && file.size > field.maxSize) {
                                                                toast.error(`File size must be less than ${(field.maxSize / 1024 / 1024).toFixed(1)}MB`);
                                                                e.target.value = '';
                                                                return;
                                                            }
                                                            ctrlField.onChange(file);
                                                        }
                                                    }}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                                                />
                                                {ctrlField.value && ctrlField.value instanceof File && (
                                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                                        <span>📎 {ctrlField.value.name}</span>
                                                        <span>({(ctrlField.value.size / 1024 / 1024).toFixed(2)} MB)</span>
                                                        <button
                                                            type="button"
                                                            onClick={() => ctrlField.onChange(null)}
                                                            className="text-red-600 hover:text-red-700 ml-2"
                                                        >
                                                            Remove
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    />
                                )}
                                {field.helperText && (
                                    <p className="text-gray-500 text-xs mt-1">{field.helperText}</p>
                                )}
                                {errors[field.name as any] && (
                                    <p className="text-red-600 text-xs mt-1">{(errors[field.name as any] as any)?.message}</p>
                                )}
                            </div>
                        ))}
                        <div className="flex gap-4">
                            <Button type="submit" disabled={isSubmitting} className="flex-1">
                                {isSubmitting ? 'Submitting...' : 'Submit Project'}
                            </Button>
                            <Button 
                                type="button" 
                                variant="secondary" 
                                onClick={downloadSubmissionBackup}
                                disabled={isSubmitting}
                            >
                                💾 Save Backup
                            </Button>
                        </div>
                    </form>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default SubmissionPage; 