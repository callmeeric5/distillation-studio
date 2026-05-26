import { useState } from 'react';

export function CollapsibleDescription({
  className = '',
  fullText,
  previewText,
}: {
  className?: string;
  fullText: string;
  previewText: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const canExpand = fullText !== previewText;

  return (
    <div className={className}>
      <p className="text-lg leading-8 text-[#5e5d59]">
        {isExpanded || !canExpand ? fullText : previewText}
      </p>
      {canExpand ? (
        <button
          className="mt-3 min-h-9 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#8a4429] transition hover:bg-[#fffdf8]"
          onClick={() => setIsExpanded((current) => !current)}
          type="button"
        >
          {isExpanded ? 'Less' : 'More'}
        </button>
      ) : null}
    </div>
  );
}
