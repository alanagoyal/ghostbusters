/**
 * Truncates a string to a maximum length, adding an ellipsis if truncated
 * @param str The string to truncate
 * @param maxLength Maximum length before truncation (default: 25)
 * @returns The truncated string with ellipsis if needed
 */
export function truncateString(str: string | null, maxLength = 25): string {
  if (!str) return '';
  return str.length > maxLength ? `${str.substring(0, maxLength)}...` : str;
}

/**
 * Converts a string to Title Case
 * @param str The string to convert
 * @returns The string in Title Case
 */
export function toTitleCase(str: string | null): string {
  if (!str) return '';
  return str
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
