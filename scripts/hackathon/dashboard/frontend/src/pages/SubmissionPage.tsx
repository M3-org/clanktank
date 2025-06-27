import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import { SubmissionInputs, SubmissionSchema, categoryOptions } from '../types/submission';
import { postSubmission, hackathonApi } from '../lib/api';
import { Button } from '../components/Button';
import { Card, CardHeader, CardContent } from '../components/Card';
import { SubmissionField, SUBMISSION_FIELDS_V2 } from '../types/submission_manifest';

const LOCAL_STORAGE_SCHEMA_KEY = 'submission_schema_v2';

const SubmissionPage: React.FC = () => {
    const navigate = useNavigate();
    const [schema, setSchema] = useState<SubmissionField[]>(SUBMISSION_FIELDS_V2);
    const [schemaError, setSchemaError] = useState<string | null>(null);
    const { 
        register, 
        control, 
        handleSubmit, 
        formState: { errors, isSubmitting },
        reset 
    } = useForm<SubmissionInputs>({ 
        resolver: yupResolver(SubmissionSchema) as any,
        defaultValues: Object.fromEntries(SUBMISSION_FIELDS_V2.map(f => [f.name, ''])) as any
    });

    // Fetch schema on mount
    useEffect(() => {
        const loadSchema = async () => {
            // Try localStorage first
            const cached = localStorage.getItem(LOCAL_STORAGE_SCHEMA_KEY);
            if (cached) {
                try {
                    setSchema(JSON.parse(cached));
                } catch {}
            }
            try {
                const remoteSchema = await hackathonApi.fetchSubmissionSchema();
                setSchema(remoteSchema);
                localStorage.setItem(LOCAL_STORAGE_SCHEMA_KEY, JSON.stringify(remoteSchema));
                setSchemaError(null);
            } catch (err) {
                setSchemaError('Could not load latest schema from server. Using fallback.');
                setSchema(SUBMISSION_FIELDS_V2);
            }
        };
        loadSchema();
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