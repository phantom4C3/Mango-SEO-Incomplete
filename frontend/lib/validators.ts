// frontend\lib\validators.ts

import type { UUID, Media, ContentItem, BlogPost } from '@/lib/types';

/** UUID validation */
export function isUUID(v: unknown): v is UUID {
  return typeof v === 'string' && /^[0-9a-fA-F-]{36}$/.test(v);
}

/** Media guard */
export function isMedia(obj: unknown): obj is Media {
  if (!obj || typeof obj !== 'object') return false;
  const o = obj as Partial<Media>;
  return isUUID(o.id) && typeof o.url === 'string' && typeof o.filename === 'string';
}

/** ContentItem guard */
export function isContentItem(obj: unknown): obj is ContentItem {
  if (!obj || typeof obj !== 'object') return false;
  const o = obj as Partial<ContentItem>;
  return isUUID(o.id) && isUUID(o.collectionId) && typeof o.data === 'object';
}

/** BlogPost guard */
export function isBlogPost(obj: unknown): obj is BlogPost {
  if (!isContentItem(obj)) return false;
  const o = obj as Partial<BlogPost>;
  return (
  typeof o.status === 'string' &&
  ['pending', 'researching', 'writing', 'enhancing', 'ready', 'published'].includes(o.status) &&
  typeof o.wordCount === 'number'
);

}

/** Safe parse ContentItem with date normalization */
export function safeParseContentItem(raw: unknown): ContentItem | null {
  if (!isContentItem(raw)) return null;
  const item = raw as ContentItem;
  if (item.createdAt && isFinite(Date.parse(item.createdAt))) {
    item.createdAt = new Date(item.createdAt).toISOString();
  }
  if (item.updatedAt && isFinite(Date.parse(item.updatedAt))) {
    item.updatedAt = new Date(item.updatedAt).toISOString();
  }
  if (item.publishedAt && isFinite(Date.parse(item.publishedAt))) {
    item.publishedAt = new Date(item.publishedAt).toISOString();
  }
  return item;
}

/** Safe parse BlogPost */
export function safeParseBlogPost(raw: unknown): BlogPost | null {
  if (!isBlogPost(raw)) return null;
  const post = safeParseContentItem(raw) as BlogPost | null;
  if (!post) return null;
  if (post.scheduledDate && isFinite(Date.parse(post.scheduledDate as any))) {
    post.scheduledDate = new Date(post.scheduledDate);
  }
  if (post.publishedDate && isFinite(Date.parse(post.publishedDate as any))) {
    post.publishedDate = new Date(post.publishedDate);
  }
  return post;
}