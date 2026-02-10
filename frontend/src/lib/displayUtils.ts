/**
 * Clean display name for candidates.
 * Handles garbage data like hashtags stored as names from LinkedIn scraping.
 */
export function cleanDisplayName(name: string | null | undefined): string {
  if (!name) return 'Unknown';
  
  let cleaned = name.trim();
  
  // Remove "on LinkedIn" or "on LinkedIn:" suffix (Google title artifact)
  cleaned = cleaned.replace(/\s+on\s+LinkedIn[:\s]?.*/i, '').trim();
  
  // If name starts with # (hashtag), it's scraped garbage
  if (cleaned.startsWith('#')) {
    return 'Unknown Poster';
  }
  
  // If name is mostly hashtags, strip them  
  const withoutHashtags = cleaned.replace(/#\w+/g, '').trim();
  if (withoutHashtags.length < 2) {
    return 'Unknown Poster';
  }
  
  // If name contains multiple hashtags, use what's left (or fallback)
  if (cleaned.includes('#')) {
    cleaned = withoutHashtags;
  }
  
  // Remove trailing LinkedIn numeric IDs (e.g., "Meenakshi Chaturvedi 5a9779326")
  cleaned = cleaned.replace(/\s+[a-f0-9]{6,}$/i, '').trim();
  
  // Clean excess whitespace
  cleaned = cleaned.replace(/\s+/g, ' ').trim();
  
  return cleaned || 'Unknown';
}

/**
 * Get the initial character for avatar display, handling garbage names.
 */
export function getNameInitial(name: string | null | undefined): string {
  const cleaned = cleanDisplayName(name);
  // Use first letter that is actually a letter
  for (const char of cleaned) {
    if (/[a-zA-Z]/.test(char)) return char.toUpperCase();
  }
  return '?';
}
