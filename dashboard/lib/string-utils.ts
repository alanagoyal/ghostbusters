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
