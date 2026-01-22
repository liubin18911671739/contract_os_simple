/**
 * LocalStorage utility functions
 * Type-safe helpers for managing settings in localStorage
 */

import { Settings, DEFAULT_SETTINGS } from '../types/settings';

const SETTINGS_KEY = 'contract_precheck_settings';

/**
 * Get a value from localStorage
 */
export function getSetting<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Error reading from localStorage (${key}):`, error);
    return defaultValue;
  }
}

/**
 * Set a value in localStorage
 */
export function setSetting<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing to localStorage (${key}):`, error);
  }
}

/**
 * Remove a value from localStorage
 */
export function removeSetting(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage (${key}):`, error);
  }
}

/**
 * Clear all settings from localStorage
 */
export function clearSettings(): void {
  try {
    localStorage.removeItem(SETTINGS_KEY);
  } catch (error) {
    console.error('Error clearing settings from localStorage:', error);
  }
}

/**
 * Get all settings from localStorage
 */
export function getSettings(): Settings {
  return getSetting<Settings>(SETTINGS_KEY, DEFAULT_SETTINGS);
}

/**
 * Save settings to localStorage (merges with existing)
 */
export function saveSettings(settings: Partial<Settings>): void {
  const current = getSettings();
  const updated = {
    ...current,
    ...settings,
    // Ensure nested objects are merged correctly
    user: settings.user ? { ...current.user, ...settings.user } : current.user,
    preferences: settings.preferences ? { ...current.preferences, ...settings.preferences } : current.preferences,
    llm: settings.llm ? { ...current.llm, ...settings.llm } : current.llm,
    kb: settings.kb ? { ...current.kb, ...settings.kb } : current.kb
  };
  setSetting(SETTINGS_KEY, updated);
}

/**
 * Reset settings to defaults
 */
export function resetSettings(): Settings {
  setSetting(SETTINGS_KEY, DEFAULT_SETTINGS);
  return DEFAULT_SETTINGS;
}
