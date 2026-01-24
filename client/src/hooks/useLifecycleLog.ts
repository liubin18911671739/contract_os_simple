/**
 * Custom hook for component lifecycle logging
 * Usage: useLifecycleLog('ComponentName', props)
 */
import { useEffect, useRef } from 'react';
import { log } from '../utils/logger';

interface LifecycleLogOptions {
  logProps?: boolean;
  logMount?: boolean;
  logUnmount?: boolean;
  logUpdate?: boolean;
  customData?: any;
}

export function useLifecycleLog(
  componentName: string,
  options: LifecycleLogOptions = {}
) {
  const {
    logProps = true,
    logMount = true,
    logUnmount = true,
    logUpdate = false,
    customData,
  } = options;

  const mountTime = useRef<number>(performance.now());
  const renderCount = useRef<number>(0);
  const previousProps = useRef<any>(undefined);

  useEffect(() => {
    renderCount.current++;

    if (logMount && renderCount.current === 1) {
      log.componentMount(componentName, customData);
    } else if (logUpdate) {
      // Check what changed
      const changes: Record<string, { from: any; to: any }> = {};
      if (previousProps.current && customData) {
        Object.keys(customData).forEach(key => {
          if (previousProps.current[key] !== customData[key]) {
            changes[key] = {
              from: previousProps.current[key],
              to: customData[key],
            };
          }
        });
      }

      if (Object.keys(changes).length > 0) {
        log.componentUpdate(componentName, {
          renderCount: renderCount.current,
          changes,
        });
      } else {
        log.componentUpdate(componentName, {
          renderCount: renderCount.current,
        });
      }
    }

    previousProps.current = customData;

    return () => {
      if (logUnmount) {
        const duration = performance.now() - mountTime.current;
        log.componentUnmount(componentName);
        log.performance(`${componentName} lifetime`, duration, 'ms');
      }
    };
  }, [componentName, logMount, logUnmount, logUpdate, customData]);

  return {
    renderCount: renderCount.current,
    mountTime: mountTime.current,
  };
}

/**
 * Hook to log async operations with timing
 */
export function useAsyncLog(operationName: string) {
  const startTiming = () => {
    log.debug(`Starting: ${operationName}`);
    return performance.now();
  };

  const endTiming = (startTime: number, result?: any) => {
    const duration = performance.now() - startTime;
    log.performance(operationName, duration, 'ms');
    return result;
  };

  const logError = (error: any) => {
    log.error(`Error in ${operationName}`, {
      error: error.message || error,
      stack: error.stack,
    });
  };

  return {
    startTiming,
    endTiming,
    logError,
  };
}

/**
 * Hook to monitor page visibility changes
 */
export function useVisibilityLog(pageName: string) {
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        log.debug(`Page hidden: ${pageName}`);
      } else {
        log.debug(`Page visible: ${pageName}`);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [pageName]);
}

/**
 * Hook to log navigation events
 */
export function useNavigationLog() {
  useEffect(() => {
    // Log initial page load
    log.info('Page loaded', {
      url: window.location.href,
      userAgent: navigator.userAgent,
      language: navigator.language,
    });

    // Log before unload
    const handleBeforeUnload = () => {
      log.info('Page unloading', {
        url: window.location.href,
      });
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);
}
