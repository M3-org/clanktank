import { hackathonApi } from './api';
import { SubmissionField } from '../types/submission';

/**
 * DYNAMIC SCHEMA LOADER
 * ====================
 * 
 * This module loads submission schema dynamically from the backend API,
 * with intelligent caching and fallback mechanisms.
 * 
 * Priority:
 * 1. Always try API first (fresh data)
 * 2. Use cached data if API fails  
 * 3. Emergency fallback if everything fails
 * 
 * Also generates Yup validation schemas dynamically from field definitions.
 */

// Emergency fallback schema (minimal fields, only used if API + cache fail)
const MINIMAL_FALLBACK_SCHEMA: SubmissionField[] = [
  { name: 'project_name', label: 'Project Name', type: 'text', required: true, placeholder: 'My Awesome Project' },
  { name: 'team_name', label: 'Team Name', type: 'text', required: true, placeholder: 'The A-Team' },
  { name: 'description', label: 'Project Description', type: 'textarea', required: true, placeholder: 'Describe your project' },
  { name: 'category', label: 'Category', type: 'select', required: true, options: ['AI/Agents', 'DeFi', 'Gaming', 'Other'] },
  { name: 'discord_handle', label: 'Discord Handle', type: 'text', required: true, placeholder: 'username#1234' },
  { name: 'github_url', label: 'GitHub URL', type: 'url', required: true, placeholder: 'https://github.com/...' },
  { name: 'demo_video_url', label: 'Demo Video URL', type: 'url', required: true, placeholder: 'https://youtube.com/...' },
];

// Cache key for localStorage
const SCHEMA_CACHE_KEY = 'hackathon_submission_schema_v2';
const SCHEMA_CACHE_EXPIRY_KEY = 'hackathon_submission_schema_v2_expiry';

// Cache duration (5 minutes - short cache for better UX)
const CACHE_DURATION_MS = 5 * 60 * 1000;

interface SchemaLoaderResult {
  schema: SubmissionField[];
  source: 'api' | 'cache' | 'fallback';
  error?: string;
}

/**
 * Load submission schema with the following priority:
 * 1. Always try API first (for fresh data)
 * 2. Use cached data only if API fails
 * 3. Fallback to hardcoded manifest as last resort
 */
export const loadSubmissionSchema = async (version: string = 'v2'): Promise<SchemaLoaderResult> => {
  // For now, only support v2 since that's what our API provides
  if (version !== 'v2') {
    return {
      schema: MINIMAL_FALLBACK_SCHEMA,
      source: 'fallback',
      error: `Version ${version} not supported, using fallback`
    };
  }

  try {
    // Always try API first for fresh data
    console.log('Fetching schema from API...');
    const apiSchema = await hackathonApi.fetchSubmissionSchema();
    
    // Validate the API response
    if (!Array.isArray(apiSchema) || apiSchema.length === 0) {
      throw new Error('Invalid schema response from API');
    }

    // Cache the successful response for offline backup
    setCachedSchema(apiSchema);

    return {
      schema: apiSchema,
      source: 'api'
    };

  } catch (error) {
    console.warn('Failed to load schema from API, trying cache...', error);
    
    // Try cache as backup
    const cachedSchema = getCachedSchema();
    if (cachedSchema) {
      return {
        schema: cachedSchema,
        source: 'cache',
        error: `API failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
    
    console.warn('No cached schema available, using fallback');
    return {
      schema: MINIMAL_FALLBACK_SCHEMA,
      source: 'fallback',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};

/**
 * Get cached schema if valid
 */
function getCachedSchema(): SubmissionField[] | null {
  try {
    const cachedSchema = localStorage.getItem(SCHEMA_CACHE_KEY);
    const cachedExpiry = localStorage.getItem(SCHEMA_CACHE_EXPIRY_KEY);

    if (!cachedSchema || !cachedExpiry) {
      return null;
    }

    const expiryTime = parseInt(cachedExpiry, 10);
    const now = Date.now();

    if (now > expiryTime) {
      // Cache expired, remove it
      localStorage.removeItem(SCHEMA_CACHE_KEY);
      localStorage.removeItem(SCHEMA_CACHE_EXPIRY_KEY);
      return null;
    }

    return JSON.parse(cachedSchema);
  } catch (error) {
    console.warn('Error reading cached schema:', error);
    // Clear corrupted cache
    localStorage.removeItem(SCHEMA_CACHE_KEY);
    localStorage.removeItem(SCHEMA_CACHE_EXPIRY_KEY);
    return null;
  }
}

/**
 * Cache schema with expiry
 */
function setCachedSchema(schema: SubmissionField[]): void {
  try {
    const expiryTime = Date.now() + CACHE_DURATION_MS;
    localStorage.setItem(SCHEMA_CACHE_KEY, JSON.stringify(schema));
    localStorage.setItem(SCHEMA_CACHE_EXPIRY_KEY, expiryTime.toString());
  } catch (error) {
    console.warn('Error caching schema:', error);
  }
}

/**
 * Force reload schema from API (bypass cache)
 */
export const reloadSubmissionSchema = async (version: string = 'v2'): Promise<SchemaLoaderResult> => {
  // Clear cache first
  localStorage.removeItem(SCHEMA_CACHE_KEY);
  localStorage.removeItem(SCHEMA_CACHE_EXPIRY_KEY);
  
  return loadSubmissionSchema(version);
};

/**
 * Create a Yup validation schema from the loaded field definitions
 */
export const createYupSchemaFromFields = async (fields: SubmissionField[]) => {
  const { object, string, mixed } = await import('yup');
  
  const schemaFields: Record<string, any> = {};
  
  fields.forEach(field => {
    let fieldSchema: any;
    
    // Handle different field types
    if (field.type === 'file') {
      // File fields use mixed() schema to accept File objects
      fieldSchema = mixed();
      
      if (field.required) {
        fieldSchema = fieldSchema.required(`${field.label} is required`);
      } else {
        fieldSchema = fieldSchema.notRequired().nullable();
      }
      
      // Add file size validation if specified
      if (field.maxSize) {
        fieldSchema = fieldSchema.test(
          'fileSize',
          `File size must be less than ${(field.maxSize / 1024 / 1024).toFixed(1)}MB`,
          (value: any) => {
            if (!value || typeof value === 'string') return true; // Allow null, undefined, or string URLs
            return value instanceof File ? value.size <= (field.maxSize || 0) : true;
          }
        );
      }
      
      // Add file type validation if specified
      if (field.accept) {
        fieldSchema = fieldSchema.test(
          'fileType',
          'Invalid file type',
          (value: any) => {
            if (!value || typeof value === 'string') return true; // Allow null, undefined, or string URLs
            if (!(value instanceof File)) return true;
            
            const acceptedTypes = field.accept?.split(',').map(t => t.trim()) || [];
            return acceptedTypes.some(type => {
              if (type.startsWith('.')) {
                return value.name.toLowerCase().endsWith(type.toLowerCase());
              } else if (type.includes('/*')) {
                const [category] = type.split('/');
                return value.type.startsWith(category);
              } else {
                return value.type === type;
              }
            });
          }
        );
      }
    } else {
      // Non-file fields use string schema
      fieldSchema = string();
      
      if (field.required) {
        fieldSchema = fieldSchema.required(`${field.label} is required`);
      } else {
        fieldSchema = fieldSchema.notRequired();
      }
      
      if (field.maxLength) {
        fieldSchema = fieldSchema.max(field.maxLength, `${field.label} must be ${field.maxLength} characters or less`);
      }
      
      if (field.type === 'url') {
        fieldSchema = fieldSchema.url('Must be a valid URL');
      }
      
      if (field.pattern) {
        const pattern = field.pattern instanceof RegExp ? field.pattern : new RegExp(field.pattern);
        fieldSchema = fieldSchema.matches(pattern, field.helperText || 'Invalid format');
      }
    }
    
    schemaFields[field.name] = fieldSchema;
  });
  
  return object(schemaFields);
}; 