/**
 * Risk Level Adjuster Component
 * Interactive component for adjusting risk levels with reason tracking
 */

import { useState } from 'react';
import { AlertTriangle, TrendingDown, TrendingUp, ChevronDown } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { adjustRiskLevel as apiAdjustRiskLevel, type RiskAdjustment } from '../../api/suggestions';

type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

interface RiskLevelAdjusterProps {
  riskId: string;
  currentLevel: RiskLevel;
  originalLevel?: RiskLevel;
  onAdjusted?: (newLevel: RiskLevel) => void;
  disabled?: boolean;
}

const LEVEL_LABELS: Record<RiskLevel, string> = {
  HIGH: '高风险',
  MEDIUM: '中风险',
  LOW: '低风险',
  INFO: '信息',
};

const LEVEL_COLORS: Record<RiskLevel, 'red' | 'amber' | 'emerald' | 'blue'> = {
  HIGH: 'red',
  MEDIUM: 'amber',
  LOW: 'emerald',
  INFO: 'blue',
};

const LEVEL_VALUES: Record<RiskLevel, number> = {
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
  INFO: 0,
};

export function RiskLevelAdjuster({
  riskId,
  currentLevel,
  originalLevel,
  onAdjusted,
  disabled = false,
}: RiskLevelAdjusterProps) {
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<RiskLevel>(currentLevel);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const hasAdjustment = originalLevel && originalLevel !== currentLevel;
  const adjustmentDirection = originalLevel
    ? LEVEL_VALUES[currentLevel] > LEVEL_VALUES[originalLevel]
      ? 'up'
      : LEVEL_VALUES[currentLevel] < LEVEL_VALUES[originalLevel]
      ? 'down'
      : null
    : null;

  const handleStartAdjust = () => {
    setSelectedLevel(currentLevel);
    setReason('');
    setError(null);
    setIsAdjusting(true);
  };

  const handleCancel = () => {
    setIsAdjusting(false);
    setSelectedLevel(currentLevel);
    setReason('');
    setError(null);
  };

  const handleSave = async () => {
    if (selectedLevel === currentLevel && !reason.trim()) {
      setIsAdjusting(false);
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const adjustment: RiskAdjustment = {
        risk_level: selectedLevel,
        reason: reason || undefined,
      };
      await apiAdjustRiskLevel(riskId, adjustment);
      onAdjusted?.(selectedLevel);
      setIsAdjusting(false);
      setReason('');
    } catch (err: any) {
      setError(err.message || '调整失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">风险等级</span>
        </div>
        {!disabled && !isAdjusting && (
          <button
            onClick={handleStartAdjust}
            className="text-xs text-accent hover:underline"
          >
            调整
          </button>
        )}
      </div>

      {/* Current level display */}
      {!isAdjusting ? (
        <div className="flex items-center gap-2">
          <Badge color={LEVEL_COLORS[currentLevel]}>{LEVEL_LABELS[currentLevel]}</Badge>
          {hasAdjustment && (
            <>
              <span className="text-xs text-gray-500">原始:</span>
              <Badge color="gray">{LEVEL_LABELS[originalLevel!]}</Badge>
              {adjustmentDirection === 'up' && (
                <TrendingUp className="w-4 h-4 text-red-500" />
              )}
              {adjustmentDirection === 'down' && (
                <TrendingDown className="w-4 h-4 text-emerald-500" />
              )}
            </>
          )}
        </div>
      ) : (
        /* Adjuster controls */
        <div className="space-y-3">
          {/* Level selector */}
          <div>
            <label className="text-xs text-gray-500 mb-1 block">选择新等级:</label>
            <div className="flex gap-2 flex-wrap">
              {(Object.keys(LEVEL_LABELS) as RiskLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => setSelectedLevel(level)}
                  disabled={disabled}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                    selectedLevel === level
                      ? 'bg-gray-800 text-white border-gray-800'
                      : 'bg-white hover:bg-gray-100 border-gray-300'
                  } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {LEVEL_LABELS[level]}
                </button>
              ))}
            </div>
          </div>

          {/* Reason input */}
          <div>
            <label className="text-xs text-gray-500 mb-1 block">
              调整原因 (可选):
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="请说明调整风险等级的原因..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent min-h-[60px] resize-y"
              disabled={isSaving}
            />
          </div>

          {/* Error message */}
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || disabled}
              className="px-3 py-1.5 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              {isSaving ? (
                <>
                  <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  保存中
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" />
                  确认调整
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact Risk Level Selector
 * Inline dropdown-style selector for risk levels
 */

interface CompactRiskLevelSelectorProps {
  value: RiskLevel;
  onChange: (level: RiskLevel) => void;
  disabled?: boolean;
  showLabel?: boolean;
}

export function CompactRiskLevelSelector({
  value,
  onChange,
  disabled = false,
  showLabel = true,
}: CompactRiskLevelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      {showLabel && (
        <label className="text-xs text-gray-500 block mb-1">风险等级:</label>
      )}
      <div className="relative">
        <button
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border transition-colors ${
            disabled
              ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
              : 'bg-white hover:bg-gray-50 border-gray-300'
          }`}
        >
          <Badge color={LEVEL_COLORS[value]}>{LEVEL_LABELS[value]}</Badge>
          <ChevronDown
            className={`w-4 h-4 text-gray-400 transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </button>

        {isOpen && !disabled && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute z-20 w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
              {(Object.keys(LEVEL_LABELS) as RiskLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => {
                    onChange(level);
                    setIsOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors flex items-center justify-between ${
                    value === level ? 'bg-gray-100' : ''
                  }`}
                >
                  <span>{LEVEL_LABELS[level]}</span>
                  {value === level && (
                    <div className="w-2 h-2 bg-accent rounded-full" />
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Risk Level Trend Indicator
 * Shows visual indicator of risk level changes
 */

interface RiskLevelTrendProps {
  from: RiskLevel;
  to: RiskLevel;
  showLabels?: boolean;
}

export function RiskLevelTrend({ from, to, showLabels = true }: RiskLevelTrendProps) {
  const diff = LEVEL_VALUES[to] - LEVEL_VALUES[from];
  const direction = diff > 0 ? 'up' : diff < 0 ? 'down' : 'unchanged';

  return (
    <div className="flex items-center gap-2">
      {showLabels && (
        <>
          <Badge color={LEVEL_COLORS[from]}>{LEVEL_LABELS[from]}</Badge>
          <span className="text-gray-400">→</span>
          <Badge color={LEVEL_COLORS[to]}>{LEVEL_LABELS[to]}</Badge>
        </>
      )}
      {direction === 'up' && (
        <TrendingUp className="w-4 h-4 text-red-500" />
      )}
      {direction === 'down' && (
        <TrendingDown className="w-4 h-4 text-emerald-500" />
      )}
    </div>
  );
}
