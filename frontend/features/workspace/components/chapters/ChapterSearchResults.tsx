"use client";

import type { ChapterSearchResult } from "@/lib/api/index";

export function ChapterSearchResults({
  isLoading,
  onOpenChapter,
  query,
  results,
}: {
  isLoading: boolean;
  onOpenChapter: (chapterId: string) => void;
  query: string;
  results: ChapterSearchResult[];
}) {
  if (isLoading) {
    return <p className="empty-note">正在搜索...</p>;
  }
  if (!results.length) {
    return <p className="empty-note">没有找到“{query.trim()}”</p>;
  }

  return (
    <div className="chapter-search-results" aria-label="章节搜索结果">
      {results.map((result) => (
        <button
          className="chapter-search-result"
          key={`${result.node_id}:${result.chapter_id}`}
          onClick={() => onOpenChapter(result.chapter_id)}
          type="button"
        >
          <strong>{result.title}</strong>
          {result.path.length ? <small>{result.path.join(" / ")}</small> : null}
          <span>{result.word_count} 字</span>
          {result.matches[0] ? <MarkedSnippet snippet={result.matches[0].snippet} /> : null}
        </button>
      ))}
    </div>
  );
}

function MarkedSnippet({ snippet }: { snippet: string }) {
  const parts = snippet.split(/(<mark>|<\/mark>)/);
  let marked = false;
  return (
    <p className="search-snippet">
      {parts.map((part, index) => {
        if (part === "<mark>") {
          marked = true;
          return null;
        }
        if (part === "</mark>") {
          marked = false;
          return null;
        }
        return marked ? <mark key={index}>{part}</mark> : <span key={index}>{part}</span>;
      })}
    </p>
  );
}
