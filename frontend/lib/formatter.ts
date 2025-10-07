// frontend/lib/utils/formatter.ts
// Utility functions for string and content formatting in MangoSEO frontend

/**
 * Capitalize the first letter of a string
 */
export function capitalizeFirstLetter(text: string): string {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Truncate a string to a given length, adding ellipsis if needed
 */
export function truncate(text: string, maxLength: number): string {
  if (!text) return '';
  return text.length > maxLength ? text.slice(0, maxLength) + '…' : text;
}

/**
 * Format number with commas as thousand separators
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Format a date object into YYYY-MM-DD format
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Capitalize every word in a string
 */
export function capitalizeWords(text: string): string {
  if (!text) return '';
  return text
    .split(' ')
    .map(word => capitalizeFirstLetter(word))
    .join(' ');
}

/**
 * Convert a string to URL-friendly slug
 */
export function slugify(text: string): string {
  if (!text) return '';
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Format an array of tags into a single comma-separated string
 */
export function formatTags(tags: string[]): string {
  if (!tags || !Array.isArray(tags)) return '';
  return tags.join(', ');
}

/**
 * Short summary of text (first N words)
 */
export function summarize(text: string, wordLimit: number): string {
  if (!text) return '';
  const words = text.split(' ');
  return words.length <= wordLimit
    ? text
    : words.slice(0, wordLimit).join(' ') + '…';
}