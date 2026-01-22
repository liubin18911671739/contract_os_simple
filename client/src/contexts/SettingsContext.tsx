/**
 * Settings Context
 * React Context for managing global settings state
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Settings, DEFAULT_SETTINGS } from '../types/settings';
import { getSettings, saveSettings, resetSettings as resetSettingsStorage } from '../utils/localStorage';

interface SettingsContextValue {
  settings: Settings;
  updateSettings: (updates: Partial<Settings>) => void;
  resetSettings: () => void;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

interface SettingsProviderProps {
  children: React.ReactNode;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = getSettings();
    setSettings(savedSettings);
    setIsInitialized(true);
  }, []);

  // Listen for changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'contract_precheck_settings' && e.newValue) {
        try {
          const newSettings = JSON.parse(e.newValue) as Settings;
          setSettings(newSettings);
        } catch (error) {
          console.error('Error parsing settings from storage event:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const updateSettings = (updates: Partial<Settings>) => {
    const updatedSettings = {
      ...settings,
      ...updates,
      // Ensure nested objects are merged correctly
      user: updates.user ? { ...settings.user, ...updates.user } : settings.user,
      preferences: updates.preferences ? { ...settings.preferences, ...updates.preferences } : settings.preferences,
      llm: updates.llm ? { ...settings.llm, ...updates.llm } : settings.llm,
      kb: updates.kb ? { ...settings.kb, ...updates.kb } : settings.kb
    };

    setSettings(updatedSettings);
    saveSettings(updates);
  };

  const resetSettings = () => {
    const defaults = resetSettingsStorage();
    setSettings(defaults);
  };

  // Don't render children until settings are loaded
  if (!isInitialized) {
    return null;
  }

  const contextValue: SettingsContextValue = {
    settings,
    updateSettings,
    resetSettings
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
}

/**
 * Custom hook to access settings context
 */
export function useSettings(): SettingsContextValue {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
