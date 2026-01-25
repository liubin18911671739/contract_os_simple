/**
 * KB Search Bar Component
 * Search input with collection filter and options
 */
import { useState } from 'react';
import { Search, X } from 'lucide-react';
import { KBCollection } from '../../api/kb';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface KBSearchBarProps {
  collections: KBCollection[];
  onSearch: (params: { query: string; collectionIds: string[]; topK: number }) => void;
  loading?: boolean;
}

export function KBSearchBar({ collections, onSearch, loading }: KBSearchBarProps) {
  const [query, setQuery] = useState('');
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<string[]>([]);
  const [topK, setTopK] = useState(6);
  const [showOptions, setShowOptions] = useState(false);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch({
        query: query.trim(),
        collectionIds: selectedCollectionIds,
        topK: topK,
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const toggleCollection = (collectionId: string) => {
    setSelectedCollectionIds(prev =>
      prev.includes(collectionId)
        ? prev.filter(id => id !== collectionId)
        : [...prev, collectionId]
    );
  };

  const clearFilters = () => {
    setSelectedCollectionIds([]);
    setTopK(6);
  };

  const hasActiveFilters = selectedCollectionIds.length > 0 || topK !== 6;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="搜索知识库..."
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowOptions(!showOptions)} variant="secondary">
            {showOptions ? '收起选项' : '筛选选项'}
            {hasActiveFilters && (
              <Badge color="blue" className="ml-2">已筛选</Badge>
            )}
          </Button>
          <Button onClick={handleSearch} disabled={!query.trim() || loading}>
            {loading ? '搜索中...' : '搜索'}
          </Button>
        </div>
      </div>

      {/* Expandable Options */}
      {showOptions && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Collection Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              知识库集合
            </label>
            <div className="flex flex-wrap gap-2">
              {collections.map(collection => (
                <button
                  key={collection.id}
                  onClick={() => toggleCollection(collection.id)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                    selectedCollectionIds.includes(collection.id)
                      ? 'bg-accent text-white border-accent'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-accent'
                  }`}
                >
                  {collection.name}
                </button>
              ))}
              {collections.length === 0 && (
                <p className="text-sm text-gray-500">暂无可用集合</p>
              )}
            </div>
          </div>

          {/* Top-K Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              返回结果数: {topK}
            </label>
            <input
              type="range"
              min="3"
              max="20"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>3</span>
              <span>20</span>
            </div>
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <div className="flex justify-end">
              <button
                onClick={clearFilters}
                className="text-sm text-accent hover:underline flex items-center gap-1"
              >
                <X className="w-3 h-3" />
                清除筛选
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
