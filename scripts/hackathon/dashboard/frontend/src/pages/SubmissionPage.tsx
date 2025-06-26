import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import { SubmissionInputs, SubmissionSchema, categoryOptions } from '../types/submission';
import { postSubmission } from '../lib/api';
import { Button } from '../components/Button';
import { Card, CardHeader, CardContent } from '../components/Card';

const SubmissionPage: React.FC = () => {
    const navigate = useNavigate();
    const { 
        register, 
        control, 
        handleSubmit, 
        formState: { errors, isSubmitting },
        reset 
    } = useForm<SubmissionInputs>({ 
        resolver: yupResolver(SubmissionSchema) as any,
        defaultValues: {
            project_name: '',
            team_name: '',
            category: '',
            description: '',
            discord_handle: '',
            twitter_handle: '',
            github_url: '',
            demo_video_url: '',
            live_demo_url: '',
            logo_url: '',
            tech_stack: '',
            how_it_works: '',
            problem_solved: '',
            coolest_tech: '',
            next_steps: '',
        }
    });

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
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                        {/* Core Project Info */}
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Core Project Info</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Project Name *
                                    </label>
                                    <input
                                        {...register('project_name')}
                                        type="text"
                                        placeholder="My Awesome Project"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.project_name && (
                                        <p className="text-red-600 text-xs mt-1">{errors.project_name.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Team Name *
                                    </label>
                                    <input
                                        {...register('team_name')}
                                        type="text"
                                        placeholder="The A-Team"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.team_name && (
                                        <p className="text-red-600 text-xs mt-1">{errors.team_name.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Category *
                                    </label>
                                    <Controller
                                        control={control}
                                        name="category"
                                        render={({ field }) => (
                                            <select
                                                {...field}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                            >
                                                <option value="">Select a category</option>
                                                {categoryOptions.map((option) => (
                                                    <option key={option} value={option}>
                                                        {option}
                                                    </option>
                                                ))}
                                            </select>
                                        )}
                                    />
                                    {errors.category && (
                                        <p className="text-red-600 text-xs mt-1">{errors.category.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Project Description *
                                    </label>
                                    <textarea
                                        {...register('description')}
                                        rows={4}
                                        placeholder="A short, clear description of what your project does."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.description && (
                                        <p className="text-red-600 text-xs mt-1">{errors.description.message}</p>
                                    )}
                                </div>
                            </div>
                        </section>

                        {/* Links & Media */}
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Links & Media</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        GitHub URL *
                                    </label>
                                    <input
                                        {...register('github_url')}
                                        type="url"
                                        placeholder="https://github.com/..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.github_url && (
                                        <p className="text-red-600 text-xs mt-1">{errors.github_url.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Demo Video URL *
                                    </label>
                                    <input
                                        {...register('demo_video_url')}
                                        type="url"
                                        placeholder="https://youtube.com/..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.demo_video_url && (
                                        <p className="text-red-600 text-xs mt-1">{errors.demo_video_url.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Live Demo URL (optional)
                                    </label>
                                    <input
                                        {...register('live_demo_url')}
                                        type="url"
                                        placeholder="https://my-project.com"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.live_demo_url && (
                                        <p className="text-red-600 text-xs mt-1">{errors.live_demo_url.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Project Logo URL (optional)
                                    </label>
                                    <input
                                        {...register('logo_url')}
                                        type="url"
                                        placeholder="https://my-project.com/logo.png"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.logo_url && (
                                        <p className="text-red-600 text-xs mt-1">{errors.logo_url.message}</p>
                                    )}
                                </div>
                            </div>
                        </section>

                        {/* Project Details */}
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Details</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Tech Stack (optional)
                                    </label>
                                    <textarea
                                        {...register('tech_stack')}
                                        rows={3}
                                        placeholder="e.g., React, Python, Solidity,..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.tech_stack && (
                                        <p className="text-red-600 text-xs mt-1">{errors.tech_stack.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        How It Works (optional)
                                    </label>
                                    <textarea
                                        {...register('how_it_works')}
                                        rows={4}
                                        placeholder="Explain the technical architecture and how the components work together."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.how_it_works && (
                                        <p className="text-red-600 text-xs mt-1">{errors.how_it_works.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Problem Solved (optional)
                                    </label>
                                    <textarea
                                        {...register('problem_solved')}
                                        rows={4}
                                        placeholder="What problem does your project solve?"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.problem_solved && (
                                        <p className="text-red-600 text-xs mt-1">{errors.problem_solved.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        What's the most impressive part of your project? (optional)
                                    </label>
                                    <textarea
                                        {...register('coolest_tech')}
                                        rows={4}
                                        placeholder="Describe the most impressive technical aspect or feature."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.coolest_tech && (
                                        <p className="text-red-600 text-xs mt-1">{errors.coolest_tech.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Next Steps (optional)
                                    </label>
                                    <textarea
                                        {...register('next_steps')}
                                        rows={3}
                                        placeholder="What are your future plans for this project?"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.next_steps && (
                                        <p className="text-red-600 text-xs mt-1">{errors.next_steps.message}</p>
                                    )}
                                </div>
                            </div>
                        </section>

                        {/* Contact Information */}
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact Information</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Discord Handle *
                                    </label>
                                    <input
                                        {...register('discord_handle')}
                                        type="text"
                                        placeholder="username#1234"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.discord_handle && (
                                        <p className="text-red-600 text-xs mt-1">{errors.discord_handle.message}</p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        X (Twitter) Handle (optional)
                                    </label>
                                    <input
                                        {...register('twitter_handle')}
                                        type="text"
                                        placeholder="@username"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.twitter_handle && (
                                        <p className="text-red-600 text-xs mt-1">{errors.twitter_handle.message}</p>
                                    )}
                                </div>
                            </div>
                        </section>

                        {/* Submit Button */}
                        <div className="pt-6 border-t border-gray-200">
                            <Button 
                                type="submit" 
                                disabled={isSubmitting}
                                size="lg"
                                className="w-full"
                            >
                                {isSubmitting ? 'Submitting...' : 'Submit Project'}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default SubmissionPage; 