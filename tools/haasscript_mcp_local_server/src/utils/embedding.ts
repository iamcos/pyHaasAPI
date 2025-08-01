import { z } from 'zod';

// Placeholder for the actual embedding logic.
// In a real scenario, this would call a Python service (our FastAPI wrapper)
// or an external embedding API (e.g., OpenAI, Cohere, Google).
export async function embed(text: string): Promise<number[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    console.log(`Attempting to fetch embedding for text: "${text.substring(0, 20)}..."`);
    console.log('Target URL: http://127.0.0.1:8000/get_embedding');

    const response = await fetch('http://127.0.0.1:8000/get_embedding', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: text }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`FastAPI embedding service returned error: ${response.status} ${response.statusText} - ${errorText}`);
      throw new Error(`FastAPI embedding service error: ${response.status} ${response.statusText}`);
    }

    const embedding: number[] = await response.json();
    console.log(`Successfully received embedding of dimension: ${embedding.length}`);
    return embedding;
  } catch (error) {
    console.error('Error calling FastAPI embedding service (caught in embed function):', error);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('FastAPI embedding service request timed out.');
      throw new Error('Embedding service timed out.');
    }
    // Log the specific error message if available
    if (error instanceof Error) {
        console.error('Detailed fetch error message:', error.message);
    } else if (typeof error === 'object' && error !== null && 'type' in error) {
        // Attempt to log properties of ErrorEvent if it's not a standard Error
        console.error('Non-standard error object details:', JSON.stringify(error, null, 2));
    }
    throw error;
  }
}

// You might also want to register an embedding tool for the MCP server itself
// if you want agents to directly request embeddings.
export function registerEmbeddingTool(mcp: any) { // Changed mcp: McpServer to mcp: any
  mcp.tool(
    'get_text_embedding',
    'Generates a vector embedding for a given text string.',
    z.object({ text: z.string() }),
    z.object({ embedding: z.array(z.number()) }),
    async ({ text }: { text: string }) => { // Explicitly type text
      const embedding = await embed(text);
      return { embedding };
    }
  );
}