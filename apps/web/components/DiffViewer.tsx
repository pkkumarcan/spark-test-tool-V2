'use client';

interface DiffLine {
  type: 'add' | 'remove' | 'context' | 'header';
  content: string;
  oldLineNum?: number;
  newLineNum?: number;
}

function parseDiff(diff: string): DiffLine[] {
  const lines = diff.split('\n');
  const result: DiffLine[] = [];
  let oldLine = 0;
  let newLine = 0;

  for (const line of lines) {
    if (line.startsWith('---') || line.startsWith('+++')) {
      result.push({ type: 'header', content: line });
    } else if (line.startsWith('@@')) {
      const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (match) {
        oldLine = parseInt(match[1], 10);
        newLine = parseInt(match[2], 10);
      }
      result.push({ type: 'header', content: line });
    } else if (line.startsWith('+')) {
      result.push({ type: 'add', content: line, newLineNum: newLine });
      newLine++;
    } else if (line.startsWith('-')) {
      result.push({ type: 'remove', content: line, oldLineNum: oldLine });
      oldLine++;
    } else {
      result.push({ type: 'context', content: line, oldLineNum: oldLine, newLineNum: newLine });
      oldLine++;
      newLine++;
    }
  }

  return result;
}

interface DiffViewerProps {
  diff: string;
  maxLines?: number;
}

export function DiffViewer({ diff, maxLines = 200 }: DiffViewerProps) {
  if (!diff) return null;

  const lines = parseDiff(diff);
  const truncated = lines.length > maxLines;
  const displayLines = truncated ? lines.slice(0, maxLines) : lines;

  return (
    <div className="rounded-md overflow-hidden border border-[#2a2a36] bg-[#0a0a12] text-xs font-mono">
      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table className="w-full border-collapse">
          <tbody>
            {displayLines.map((line, i) => (
              <tr
                key={i}
                className={
                  line.type === 'add'
                    ? 'bg-[rgba(34,197,94,0.12)]'
                    : line.type === 'remove'
                      ? 'bg-[rgba(239,68,68,0.12)]'
                      : line.type === 'header'
                        ? 'bg-[#1a1a22]'
                        : ''
                }
              >
                {line.type !== 'header' ? (
                  <>
                    <td className="w-12 text-right pr-2 select-none text-[#555] py-0.5 px-2">
                      {line.oldLineNum ?? ''}
                    </td>
                    <td className="w-12 text-right pr-2 select-none text-[#555] py-0.5 px-2">
                      {line.newLineNum ?? ''}
                    </td>
                    <td
                      className={`py-0.5 px-2 whitespace-pre ${
                        line.type === 'add'
                          ? 'text-[#4ade80]'
                          : line.type === 'remove'
                            ? 'text-[#f87171]'
                            : 'text-[#aaa]'
                      }`}
                    >
                      {line.content}
                    </td>
                  </>
                ) : (
                  <td
                    colSpan={3}
                    className="py-1 px-2 text-[#7a7a8e] select-none"
                  >
                    {line.content}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {truncated && (
        <div className="px-3 py-1.5 bg-[#1a1a22] text-[#7a7a8e] text-[10px] border-t border-[#2a2a36]">
          Showing {maxLines} of {lines.length} lines
        </div>
      )}
    </div>
  );
}
