/**
 * Logger utility for frontend debugging
 * Provides different log levels and structured logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: any;
}

class Logger {
  private isDevelopment = import.meta.env.DEV;
  private logLevel: LogLevel = 'info';
  private logs: Array<{ level: LogLevel; timestamp: Date; message: string; context?: LogContext }> = [];

  // Log level priorities
  private levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  private shouldLog(level: LogLevel): boolean {
    return this.levelPriority[level] >= this.levelPriority[this.logLevel];
  }

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';
    return `${prefix} ${message}${contextStr}`;
  }

  private log(level: LogLevel, message: string, context?: LogContext) {
    if (!this.isDevelopment || !this.shouldLog(level)) return;

    const timestamp = new Date();
    const formattedMessage = this.formatMessage(level, message, context);

    // Store log in memory (max 100 logs)
    this.logs.push({ level, timestamp, message, context });
    if (this.logs.length > 100) {
      this.logs.shift();
    }

    // Console output with colors
    const style = this.getConsoleStyle(level);
    const consoleMethod = this.getConsoleMethod(level);

    consoleMethod(
      `%c${formattedMessage}`,
      style,
      context ? '' : ''
    );

    // Log context separately if present
    if (context) {
      consoleMethod('Context:', context);
    }
  }

  private getConsoleStyle(level: LogLevel): string {
    const styles = {
      debug: 'color: #888; font-weight: normal;',
      info: 'color: #007acc; font-weight: normal;',
      warn: 'color: #ff9800; font-weight: bold;',
      error: 'color: #f44336; font-weight: bold;',
    };
    return styles[level];
  }

  private getConsoleMethod(level: LogLevel): (...args: any[]) => void {
    const methods = {
      debug: console.debug,
      info: console.info,
      warn: console.warn,
      error: console.error,
    };
    return methods[level];
  }

  /** Log debug message */
  debug(message: string, context?: LogContext) {
    this.log('debug', message, context);
  }

  /** Log info message */
  info(message: string, context?: LogContext) {
    this.log('info', message, context);
  }

  /** Log warning message */
  warn(message: string, context?: LogContext) {
    this.log('warn', message, context);
  }

  /** Log error message */
  error(message: string, context?: LogContext) {
    this.log('error', message, context);
  }

  /** Log API request */
  apiRequest(method: string, path: string, data?: any) {
    this.debug(`API Request: ${method} ${path}`, data ? { data } : undefined);
  }

  /** Log API response */
  apiResponse(method: string, path: string, status: number, duration: number) {
    const isSuccess = status >= 200 && status < 300;
    const logLevel: LogLevel = isSuccess ? 'debug' : 'warn';
    this.log(logLevel, `API Response: ${method} ${path} - ${status} (${duration}ms)`, {
      status,
      duration: `${duration}ms`,
      success: isSuccess,
    });
  }

  /** Log API error */
  apiError(method: string, path: string, error: any, duration?: number) {
    this.error(`API Error: ${method} ${path}`, {
      error: error.message || error,
      status: error.status,
      duration: duration ? `${duration}ms` : undefined,
    });
  }

  /** Log page navigation */
  navigation(from: string, to: string) {
    this.info(`Navigation: ${from} -> ${to}`);
  }

  /** Log component lifecycle */
  componentMount(componentName: string, props?: any) {
    this.debug(`Component mounted: ${componentName}`, props ? { props } : undefined);
  }

  componentUnmount(componentName: string) {
    this.debug(`Component unmounted: ${componentName}`);
  }

  componentUpdate(componentName: string, changes?: any) {
    this.debug(`Component updated: ${componentName}`, changes ? { changes } : undefined);
  }

  /** Log performance metric */
  performance(metric: string, value: number, unit: 'ms' | 'bytes' | 'count' = 'ms') {
    this.info(`Performance: ${metric} = ${value}${unit}`, { metric, value, unit });
  }

  /** Set log level */
  setLogLevel(level: LogLevel) {
    this.logLevel = level;
    this.info(`Log level set to: ${level}`);
  }

  /** Get all logs */
  getLogs() {
    return [...this.logs];
  }

  /** Clear logs */
  clearLogs() {
    this.logs = [];
    this.info('Logs cleared');
  }

  /** Export logs as JSON */
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  /** Download logs as file */
  downloadLogs() {
    const data = this.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    this.info('Logs downloaded');
  }
}

// Global logger instance
export const logger = new Logger();

// Export convenience functions
export const log = {
  debug: (message: string, context?: LogContext) => logger.debug(message, context),
  info: (message: string, context?: LogContext) => logger.info(message, context),
  warn: (message: string, context?: LogContext) => logger.warn(message, context),
  error: (message: string, context?: LogContext) => logger.error(message, context),
  apiRequest: (method: string, path: string, data?: any) => logger.apiRequest(method, path, data),
  apiResponse: (method: string, path: string, status: number, duration: number) =>
    logger.apiResponse(method, path, status, duration),
  apiError: (method: string, path: string, error: any, duration?: number) =>
    logger.apiError(method, path, error, duration),
  navigation: (from: string, to: string) => logger.navigation(from, to),
  componentMount: (name: string, props?: any) => logger.componentMount(name, props),
  componentUnmount: (name: string) => logger.componentUnmount(name),
  componentUpdate: (name: string, changes?: any) => logger.componentUpdate(name, changes),
  performance: (metric: string, value: number, unit?: 'ms' | 'bytes' | 'count') =>
    logger.performance(metric, value, unit),
};

// Make logger available globally for debugging
if (import.meta.env.DEV) {
  (window as any).logger = logger;
  (window as any).log = log;
  console.info('Logger initialized. Access via window.logger or window.log');
}
