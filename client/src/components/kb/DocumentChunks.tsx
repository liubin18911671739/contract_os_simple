/**
 * Document Chunks Component
 * Displays all chunks for a document with pagination
 */
import { useState } from 'react';
import { KBChunk } from '../../api/kb';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface DocumentChunksProps {
  chunks: KBChunk[];
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

const CHUNKS_PER_PAGE = 10;

export function DocumentChunks({ chunks, documentTitle, onClose }: DocumentChunksProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredChunks = searchQuery
    ? chunks.filter(c =>
        c.text.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : chunks;

  const totalPages = Math.ceil(filteredChunks.length / CHUNKS_PER_PAGE);
  const startIndex = currentPage * CHUNKS_PER_PAGE;
  const endIndex = startIndex + CHUNKS_PER_PAGE;
  const currentChunks = filteredChunks.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(0, Math.min(page, totalPages - 1)));
  };

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{documentTitle}</h3>
          <p className="text-sm text-gray-500 mt-1">
            共 {chunks.length} 个片段 {filteredChunks.length !== chunks.length && `(筛选: ${filteredChunks.length})`}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Search */}
      <div className="px-6 pt-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索片段内容..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(0);
            }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>
      </div>

      {/* Chunks List */}
      <div className="max-h-96 overflow-y-auto">
        {currentChunks.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {searchQuery ? '未找到匹配的片段' : '该文档暂无片段'}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {currentChunks.map((chunk) => (
              <div key={chunk.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono text-gray-500">
                        片段 #{chunk.chunk_index + 1}
                      </span>
                      {chunk.is_indexed ? (
                        <Badge color="emerald">已索引</Badge>
                      ) : (
                        <Badge color="gray">未索引</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {chunk.text}
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {chunk.text.length} 字符
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            显示 {startIndex + 1}-{Math.min(endIndex, filteredChunks.length)} / 共 {filteredChunks.length}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-gray-600">
              第 {currentPage + 1} / {totalPages} 页
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
