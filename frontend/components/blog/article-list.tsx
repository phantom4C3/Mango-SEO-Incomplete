/**
 * Article List Component - Displays a paginated, filterable list of blog articles
 * Supports search, sorting, filtering, and bulk actions
 * Designed for dark theme with mango yellow accents
 */

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/custom-ui/extras/card';
import { Button } from '@/components/custom-ui/extras/button';
;
import { Badge } from '@/components/custom-ui/extras/badge';
import { Input } from '@/components/custom-ui/extras/input';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/custom-ui/extras/select';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  ChevronLeft, 
  ChevronRight,
  Calendar,
  Eye,
  Edit,
  Trash2,
  Download,
  Plus
} from 'lucide-react';
import { Article, ArticleStatus, ArticleFilterParams } from '@/types';
import { cn } from '@/lib/utils';
import { ArticleCard } from './article-card';
import { ArticleGrid } from './article-grid';

interface ArticleListProps {
  articles: Article[];
  loading?: boolean;
  onEdit?: (article: Article) => void;
  onDelete?: (article: Article) => void;
  onView?: (article: Article) => void;
  onExport?: (articles: Article[]) => void;
  onCreate?: () => void;
  className?: string;
  showActions?: boolean;
  pagination?: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    itemsPerPage: number;
    onPageChange: (page: number) => void;
    onItemsPerPageChange?: (itemsPerPage: number) => void;
  };
  filters?: ArticleFilterParams;
  onFiltersChange?: (filters: ArticleFilterParams) => void;
}

export const ArticleList: React.FC<ArticleListProps> = ({
  articles,
  loading = false,
  onEdit,
  onDelete,
  onView,
  onExport,
  onCreate,
  className,
  showActions = true,
  pagination,
  filters,
  onFiltersChange
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedArticles, setSelectedArticles] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState(filters?.search || '');
  const [statusFilter, setStatusFilter] = useState<ArticleStatus | 'all'>(filters?.status || 'all');

  // Filter and sort articles based on current filters
  const filteredArticles = useMemo(() => {
    let filtered = articles;

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(article => 
        article.title.toLowerCase().includes(query) ||
        article.target_keyword?.toLowerCase().includes(query) ||
        article.content?.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(article => article.status === statusFilter);
    }

    // Apply date filters
    if (filters?.from_date) {
      const fromDate = new Date(filters.from_date);
      filtered = filtered.filter(article => 
        new Date(article.created_at) >= fromDate
      );
    }

    if (filters?.to_date) {
      const toDate = new Date(filters.to_date);
      toDate.setHours(23, 59, 59, 999);
      filtered = filtered.filter(article => 
        new Date(article.created_at) <= toDate
      );
    }

    // Apply sorting
    if (filters?.sort_by) {
      filtered.sort((a, b) => {
        const aValue = a[filters.sort_by as keyof Article];
        const bValue = b[filters.sort_by as keyof Article];
        
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return filters.sort_order === 'desc' 
            ? bValue.localeCompare(aValue)
            : aValue.localeCompare(bValue);
        }
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return filters.sort_order === 'desc' 
            ? bValue - aValue
            : aValue - aValue;
        }
        
        return 0;
      });
    }

    return filtered;
  }, [articles, searchQuery, statusFilter, filters]);

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    onFiltersChange?.({ ...filters, search: value });
  };

  const handleStatusFilterChange = (value: ArticleStatus | 'all') => {
    setStatusFilter(value);
    onFiltersChange?.({ 
      ...filters, 
      status: value === 'all' ? undefined : value 
    });
  };

  const handleSelectArticle = (articleId: string) => {
    const newSelected = new Set(selectedArticles);
    if (newSelected.has(articleId)) {
      newSelected.delete(articleId);
    } else {
      newSelected.add(articleId);
    }
    setSelectedArticles(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedArticles.size === filteredArticles.length) {
      setSelectedArticles(new Set());
    } else {
      setSelectedArticles(new Set(filteredArticles.map(article => article.id)));
    }
  };

  const handleBulkExport = () => {
    const selected = articles.filter(article => selectedArticles.has(article.id));
    onExport?.(selected);
  };

  const handleBulkDelete = () => {
    const selected = articles.filter(article => selectedArticles.has(article.id));
    selected.forEach(article => onDelete?.(article));
    setSelectedArticles(new Set());
  };

  const statusOptions: { value: ArticleStatus | 'all'; label: string; color: string }[] = [
    { value: 'all', label: 'All Articles', color: 'text-gray-400' },
    { value: 'draft', label: 'Drafts', color: 'text-yellow-400' },
    { value: 'published', label: 'Published', color: 'text-green-400' },
    { value: 'scheduled', label: 'Scheduled', color: 'text-blue-400' },
    { value: 'error', label: 'Errors', color: 'text-red-400' }
  ];

  if (loading) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-800 rounded w-48 animate-pulse"></div>
          <div className="flex gap-2">
            <div className="h-9 w-9 bg-gray-800 rounded animate-pulse"></div>
            <div className="h-9 w-9 bg-gray-800 rounded animate-pulse"></div>
            <div className="h-9 w-28 bg-gray-800 rounded animate-pulse"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="bg-gray-900 border-gray-800 animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-800 rounded mb-4"></div>
                <div className="h-3 bg-gray-800 rounded mb-2"></div>
                <div className="h-3 bg-gray-800 rounded w-2/3"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with Controls */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-white">Blog Articles</CardTitle>
              <CardDescription className="text-gray-400">
                {filteredArticles.length} articles found
                {searchQuery && ` for "${searchQuery}"`}
                {statusFilter !== 'all' && ` in ${statusFilter}`}
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                className="bg-yellow-500 text-gray-900 hover:bg-yellow-400"
                onClick={onCreate}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Article
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Search and Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10 bg-gray-800 border-gray-700 text-white placeholder-gray-500"
              />
            </div>

            <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
              <SelectTrigger className="w-full sm:w-48 bg-gray-800 border-gray-700 text-white">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent className="bg-gray-900 border-gray-800 text-white">
                {statusOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <span className={option.color}>{option.label}</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                className={cn(
                  "border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800",
                  viewMode === 'grid' && "bg-gray-800 text-yellow-400 border-yellow-500/50"
                )}
                onClick={() => setViewMode('grid')}
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className={cn(
                  "border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800",
                  viewMode === 'list' && "bg-gray-800 text-yellow-400 border-yellow-500/50"
                )}
                onClick={() => setViewMode('list')}
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedArticles.size > 0 && (
            <div className="flex items-center gap-4 p-4 mb-6 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <span className="text-yellow-400 text-sm">
                {selectedArticles.size} article{selectedArticles.size !== 1 ? 's' : ''} selected
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/20"
                  onClick={handleBulkExport}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export Selected
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-red-500/50 text-red-400 hover:bg-red-500/20"
                  onClick={handleBulkDelete}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Selected
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-400 hover:text-white"
                  onClick={() => setSelectedArticles(new Set())}
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Articles Display */}
      {filteredArticles.length === 0 ? (
        <Card className="bg-gray-900 border-gray-800 text-center py-12">
          <CardContent>
            <div className="text-gray-400 mb-4">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium text-white mb-2">No articles found</h3>
              <p className="text-gray-400">
                {searchQuery || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Get started by creating your first article'
                }
              </p>
            </div>
            {!searchQuery && statusFilter === 'all' && onCreate && (
              <Button
                className="bg-yellow-500 text-gray-900 hover:bg-yellow-400"
                onClick={onCreate}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Article
              </Button>
            )}
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        <ArticleGrid
          articles={filteredArticles}
          selectedArticles={selectedArticles}
          onSelect={handleSelectArticle}
          onEdit={onEdit}
          onDelete={onDelete}
          onView={onView}
        />
      ) : (
        <div className="space-y-4">
          {filteredArticles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              selected={selectedArticles.has(article.id)}
              onSelect={handleSelectArticle}
              onEdit={onEdit}
              onDelete={onDelete}
              onView={onView}
              variant="list"
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.totalPages > 1 && (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-400">
                Showing {((pagination.currentPage - 1) * pagination.itemsPerPage) + 1} to{' '}
                {Math.min(pagination.currentPage * pagination.itemsPerPage, pagination.totalItems)} of{' '}
                {pagination.totalItems} articles
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800"
                  disabled={pagination.currentPage === 1}
                  onClick={() => pagination.onPageChange(pagination.currentPage - 1)}
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Previous
                </Button>
                
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                    const page = i + 1;
                    return (
                      <Button
                        key={page}
                        variant={pagination.currentPage === page ? "default" : "outline"}
                        size="sm"
                        className={cn(
                          "min-w-9 h-9 p-0",
                          pagination.currentPage === page 
                            ? "bg-yellow-500 text-gray-900 hover:bg-yellow-400" 
                            : "border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800"
                        )}
                        onClick={() => pagination.onPageChange(page)}
                      >
                        {page}
                      </Button>
                    );
                  })}
                  
                  {pagination.totalPages > 5 && (
                    <span className="px-2 text-gray-400">...</span>
                  )}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  className="border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800"
                  disabled={pagination.currentPage === pagination.totalPages}
                  onClick={() => pagination.onPageChange(pagination.currentPage + 1)}
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};