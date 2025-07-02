import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import { SubmissionInputs, SubmissionSchema } from '../types/submission';
import { postSubmission } from '../lib/api';
import { Button } from '../components/Button';
import { Card, CardHeader, CardContent } from '../components/Card';
import { SubmissionField, loadSubmissionSchema, createYupSchemaFromFields } from '../lib/schemaLoader';

const SubmissionPage: React.FC = () => {
    const navigate = useNavigate();
    const [schema, setSchema] = useState<SubmissionField[]>([]);
    const [schemaError, setSchemaError] = useState<string | null>(null);
    const [validationSchema, setValidationSchema] = useState<any>(SubmissionSchema);
    const [schemaSource, setSchemaSource] = useState<'api' | 'cache' | 'fallback'>('fallback');
    
    const { 
        register, 
        control, 
        handleSubmit, 
        formState: { errors, isSubmitting },
        reset 
    } = useForm<SubmissionInputs>({ 
        resolver: yupResolver(validationSchema) as any,
        defaultValues: Object.fromEntries(schema.map(f => [f.name, ''])) as any
    });

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
                
            } catch (error) {
                console.error('Failed to initialize schema:', error);
                setSchemaError('Failed to load schema, using minimal fallback');
                // Use a minimal fallback if everything fails
                setSchema([
                    { name: 'project_name', label: 'Project Name', type: 'text', required: true, placeholder: 'My Awesome Project' },
                    { name: 'team_name', label: 'Team Name', type: 'text', required: true, placeholder: 'The A-Team' },
                    { name: 'description', label: 'Project Description', type: 'textarea', required: true, placeholder: 'Describe your project' },
                ]);
                setSchemaSource('fallback');
            }
        };
        
        initializeSchema();
    }, []);

    const onSubmit = async (data: SubmissionInputs) => {
        try {
            const response = await postSubmission(data);
            console.log('Submission response:', response);
            
            if (response.submission_id) {
                toast.success(`Submission successful! Your submission ID is: ${response.submission_id}`);
                reset();
                navigate(`/submission/${response.submission_id}`, { replace: true });
            } else {
                toast.success('Submission successful! Check the dashboard for your entry.');
                reset();
                navigate('/', { replace: true });
            }
        } catch (error: any) {
            console.error('Submission error:', error);
            
            if (error.response?.status === 429) {
                toast.error("Slow down, you're submitting too fast. Please try again in a moment.");
            } else if (error.response?.status === 422) {
                // Handle Pydantic validation errors
                const errorData = error.response.data;
                if (errorData.detail && Array.isArray(errorData.detail)) {
                    errorData.detail.forEach((validationError: any) => {
                        const field = validationError.loc?.[validationError.loc.length - 1];
                        const message = validationError.msg;
                        if (field) {
                            toast.error(`${field}: ${message}`);
                        }
                    });
                } else {
                    toast.error('Please check your form inputs and try again.');
                }
            } else {
                toast.error('An error occurred while submitting. Please try again.');
            }
        }
    };

    return (
        <div className="p-4 md:p-10">
            <Toaster position="top-right" />
            <Card className="max-w-4xl mx-auto">
                <CardHeader>
                    <h1 className="text-2xl font-bold text-gray-900">Submit Your Hackathon Project</h1>
                    <p className="mt-2 text-gray-600">
                        Fill out the details below to enter your project into the Clank Tank Hackathon. 
                        All fields with an * are required.
                    </p>
                    {schemaError && (
                        <p className="text-yellow-600 text-sm mt-2">{schemaError}</p>
                    )}
                    {schemaSource && (
                        <p className="text-gray-500 text-xs mt-1">
                            Schema source: {schemaSource === 'api' ? '🔄 Live API' : schemaSource === 'cache' ? '💾 Cached' : '📦 Fallback'}
                        </p>
                    )}
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                        {/* Render fields dynamically from schema */}
                        {schema.map(field => (
                            <div key={field.name} className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {field.label}{field.required ? ' *' : ''}
                                </label>
                                {field.type === 'text' && (
                                    <input
                                        {...register(field.name as keyof SubmissionInputs)}
                                        type="text"
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'url' && (
                                    <input
                                        {...register(field.name as keyof SubmissionInputs)}
                                        type="url"
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'textarea' && (
                                    <textarea
                                        {...register(field.name as keyof SubmissionInputs)}
                                        rows={field.maxLength && field.maxLength > 500 ? 4 : 3}
                                        placeholder={field.placeholder}
                                        maxLength={field.maxLength}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                )}
                                {field.type === 'select' && Array.isArray(field.options) && (
                                    <Controller
                                        control={control}
                                        name={field.name as keyof SubmissionInputs}
                                        render={({ field: ctrlField }) => (
                                            <select
                                                {...ctrlField}
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
                                {field.helperText && (
                                    <p className="text-gray-500 text-xs mt-1">{field.helperText}</p>
                                )}
                                {errors[field.name as keyof SubmissionInputs] && (
                                    <p className="text-red-600 text-xs mt-1">{(errors[field.name as keyof SubmissionInputs] as any)?.message}</p>
                                )}
                            </div>
                        ))}
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Submitting...' : 'Submit Project'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default SubmissionPage; 