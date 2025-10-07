/**
 * Article Card Component - Individual article display card
 * Used in both grid and list views
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/custom-ui/extras/card';
import { Button } from '@/components/custom-ui/extras/button';
;
import { Badge } from '@/components/custom-ui/extras/badge';
import { Checkbox } from '@/components/custom-ui/extras/checkbox';
import { Calendar, Eye, Edit, Trash2, ExternalLink } from 'lucide-react';
import { Article, ArticleStatus } from '@/types';
import { cn } from '@/lib/utils';

interface ArticleCardProps {
  article: Article;
  selected?: boolean;
  onSelect?: (articleId: string) => void;
  onEdit?: (article: Article) => void;
  onDelete?: (article: Article) => void;
  onView?: (article: Article) => void;
  variant?: 'grid' | 'list';
}

export const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  selected = false,
  onSelect,
  onEdit,
  onDelete,
  onView,
  variant = 'grid'
}) => {
  const statusColors: Record<ArticleStatus, string> = {
    draft: 'text-yellow-400 bg-yellow-500/10',
    published: 'text-green-400 bg-green-500/10',
    scheduled: 'text-blue-400 bg-blue-500/10',
    error: 'text-red-400 bg-red-500/10'
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Card className={cn(
      "bg-gray-900 border-gray-800 transition-all hover:border-gray-700",
      selected && "border-yellow-500/50 bg-yellow-500/5",
      variant === 'list' && "flex items-center"
    )}>
      <CardContent className={cn("p-4", variant === 'list' && "flex items-center gap-4 flex-1")}>
        {/* Selection Checkbox */}
        {onSelect && (
          <Checkbox
            checked={selected}
            onCheckedChange={() => onSelect(article.id)}
            className="border-gray-700 data-[state=checked]:bg-yellow-500 data-[state=checked]:border-yellow-500"
          />
        )}

        {/* Article Content */}
        <div className={cn("flex-1", variant === 'list' && "flex items-center gap-4")}>
          {/* Thumbnail placeholder */}
          {variant === 'grid' && (
            <div className="w-full h-48 bg-gray-800 rounded-lg mb-4 flex items-center justify-center">
              <div className="text-gray-600 text-sm">No image</div>
            </div>
          )}

          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="text-white font-medium line-clamp-2 mb-1">
                  {article.title}
                </h3>
                {article.target_keyword && (
                  <p className="text-yellow-400 text-sm mb-2">
                    {article.target_keyword}
                  </p>
                )}
              </div>
              
              <Badge className={cn(statusColors[article.status], "capitalize")}>
                {article.status}
              </Badge>
            </div>

            {article.meta_description && variant === 'grid' && (
              <p className="text-gray-400 text-sm line-clamp-3 mb-3">
                {article.meta_description}
              </p>
            )}

            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {formatDate(article.created_at)}
                </span>
                {article.word_count && (
                  <span>{article.word_count.toLocaleString()} words</span>
                )}
                {article.seo_score && (
                  <span className="text-yellow-400">SEO: {article.seo_score}</span>
                )}
              </div>

              <div className="flex items-center gap-1">
                {onView && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-gray-400 hover:text-white"
                    onClick={() => onView(article)}
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                )}
                {onEdit && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-gray-400 hover:text-yellow-400"
                    onClick={() => onEdit(article)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-gray-400 hover:text-red-400"
                    onClick={() => onDelete(article)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
                {article.published_url && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-gray-400 hover:text-blue-400"
                    asChild
                  >
                    <a href={article.published_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

