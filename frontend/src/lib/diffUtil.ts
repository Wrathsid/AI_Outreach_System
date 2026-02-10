/**
 * U4: Draft diff highlighting utility.
 * Computes a simple word-level diff between two draft strings,
 * returning segments marked as added, removed, or unchanged.
 */

export interface DiffSegment {
  type: 'added' | 'removed' | 'unchanged';
  text: string;
}

/**
 * Compute a word-level diff between the old and new versions of a draft.
 * Uses a simple LCS-based approach suitable for short texts (< 500 words).
 */
export function computeDraftDiff(oldText: string, newText: string): DiffSegment[] {
  if (!oldText && !newText) return [];
  if (!oldText) return [{ type: 'added', text: newText }];
  if (!newText) return [{ type: 'removed', text: oldText }];

  const oldWords = oldText.split(/(\s+)/);
  const newWords = newText.split(/(\s+)/);

  // Build LCS table
  const m = oldWords.length;
  const n = newWords.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldWords[i - 1] === newWords[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to produce diff segments
  const segments: DiffSegment[] = [];
  let i = m, j = n;

  const rawSegments: DiffSegment[] = [];
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i - 1] === newWords[j - 1]) {
      rawSegments.push({ type: 'unchanged', text: oldWords[i - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rawSegments.push({ type: 'added', text: newWords[j - 1] });
      j--;
    } else {
      rawSegments.push({ type: 'removed', text: oldWords[i - 1] });
      i--;
    }
  }

  rawSegments.reverse();

  // Merge consecutive segments of the same type for cleaner output
  for (const seg of rawSegments) {
    const last = segments[segments.length - 1];
    if (last && last.type === seg.type) {
      last.text += seg.text;
    } else {
      segments.push({ ...seg });
    }
  }

  return segments;
}

/**
 * Render diff segments as an HTML string with inline highlighting.
 * Green for added, red/strikethrough for removed.
 */
export function renderDiffAsHtml(segments: DiffSegment[]): string {
  return segments
    .map((seg) => {
      switch (seg.type) {
        case 'added':
          return `<span style="background:rgba(34,197,94,0.15);color:#22c55e;">${escapeHtml(seg.text)}</span>`;
        case 'removed':
          return `<span style="background:rgba(239,68,68,0.15);color:#ef4444;text-decoration:line-through;">${escapeHtml(seg.text)}</span>`;
        default:
          return escapeHtml(seg.text);
      }
    })
    .join('');
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
