// Dead-simple singleton cache for configuration
export const configPromise = fetch('/api/config').then(r => {
  if (!r.ok) throw new Error(`Config fetch failed: ${r.status}`);
  return r.json();
});

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
    const config: ConfigData = await configPromise;
    
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