/**
 * API utilities for Rayansh's Personal AI Chat
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  timestamp: string;
  response_time: string;
  model: string;
}

/**
 * Send a chat message to the AI
 */
export async function sendMessage(
  message: string,
  sessionId?: string,
  userName?: string
): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_name: userName,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

/**
 * Clear chat session
 */
export async function clearSession(sessionId: string): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/chat/clear/${sessionId}`, {
      method: 'POST',
    });
  } catch (error) {
    console.error('Error clearing session:', error);
    throw error;
  }
}

/**
 * Get AI status
 */
export async function getStatus(): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`);
    return await response.json();
  } catch (error) {
    console.error('Error getting status:', error);
    throw error;
  }
}

/**
 * Generate a unique session ID
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}
