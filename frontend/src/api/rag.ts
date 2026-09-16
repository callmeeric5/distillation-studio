export type RagAnswerPayload = {
  question: string;
  k: number;
};

export type RagSource = {
  file_path: string;
  first_character_index: number;
  last_character_index: number;
  content: string;
};

export type RagAnswerResponse = {
  question: string;
  answer: string;
  sources: RagSource[];
};

export async function answerRagQuestion(payload: RagAnswerPayload) {
  const response = await fetch('/api/projects/rag/answer', {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    const preview = text.replace(/\s+/g, ' ').trim().slice(0, 160);
    throw new Error(
      response.ok
        ? 'RAG API returned a non-JSON response.'
        : `RAG API proxy returned HTTP ${response.status}. ${preview}`,
    );
  }

  const data = (await response.json()) as RagAnswerResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not answer the question.');
  return data;
}
