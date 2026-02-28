import { hackathonApi } from './api'

// Cache config data globally with proper axios caching  
let configPromise: Promise<any> | null = null

export function getConfigPromise() {
  if (!configPromise) {
    configPromise = hackathonApi.getConfig()
  }
  return configPromise
}

interface ConfigData {
  submission_deadline: string | null;
  current_time: string;
  can_submit: boolean;
  submission_window_open: boolean;
}

interface DeadlineConfig {
  deadline: string | null;
  epoch: number;
  canSubmit: boolean;
}

// Use anywhere without providers
export async function getDeadlineConfig(): Promise<DeadlineConfig> {
  try {
    const config: ConfigData = await getConfigPromise();
    
    // Calculate server epoch once for monotonic time
    const serverTime = new Date(config.current_time).getTime();
    const epoch = serverTime - performance.now();
    
    return {
      deadline: config.submission_deadline,
      epoch,
      canSubmit: config.can_submit // Let backend handle grace periods
    };
  } catch (err) {
    console.error('Failed to fetch deadline:', err);
    return { 
      deadline: null, 
      epoch: Date.now() - performance.now(), 
      canSubmit: false 
    };
  }
}