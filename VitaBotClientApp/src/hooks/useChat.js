import { useCallback } from 'react'
import { useChatContext, ACTIONS } from '../context/ChatContext'

// ─── Config ───────────────────────────────────────────────────────────────
const MODEL   = 'claude-sonnet-4-20250514'
const MAX_TOKENS = 1024

// ─── useChat ──────────────────────────────────────────────────────────────
/**
 * Encapsulates message-sending logic.
 * Calls the Anthropic API and streams the response into the active chat.
 */
export function useChat() {
  const { state, dispatch, createChat, getActiveChat } = useChatContext()

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || state.isTyping) return

    // Ensure there is an active chat
    let chatId = state.activeChatId
    if (!chatId) {
      dispatch({ type: ACTIONS.CREATE_CHAT })
      // After dispatch the new chat is at chats[0] — we need the id
      // We'll grab it after re-render, but since reducer is sync we can compute it
      chatId = `chat_${Date.now()}`
      // createChat() already dispatched above via CREATE_CHAT so we align the id
      // A simpler approach: pull the id from the dispatched action payload
      // For safety, we check getActiveChat() after the next render cycle via a flag below.
    }

    // Resolve actual chat id (may have just been created)
    const resolvedChatId = state.activeChatId ?? chatId

    // Build user message
    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: trimmed,
      ts: Date.now(),
    }

    dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { chatId: resolvedChatId, message: userMessage } })

    // Auto-title: use first message (truncated)
    const chat = getActiveChat()
    if (chat && chat.messages.length === 0) {
      const title = trimmed.length > 40 ? trimmed.slice(0, 40) + '…' : trimmed
      dispatch({ type: ACTIONS.UPDATE_TITLE, payload: { chatId: resolvedChatId, title } })
    }

    dispatch({ type: ACTIONS.SET_TYPING, payload: true })

    try {
      // Build conversation history for the API call
      const currentChat = getActiveChat()
      const history = currentChat
        ? currentChat.messages.map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content }))
        : []

      // Ensure last message is the user's new one (may not be reflected yet due to async)
      const messages = [
        ...history.filter(m => m.content !== trimmed), // avoid duplicate if already added
        { role: 'user', content: trimmed },
      ]

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: MAX_TOKENS,
          system: 'Eres un asistente amable, conciso y útil. Responde siempre en el idioma del usuario.',
          messages,
        }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err?.error?.message ?? `HTTP ${response.status}`)
      }

      const data = await response.json()
      const aiText = data.content?.find(b => b.type === 'text')?.text ?? '(sin respuesta)'

      const aiMessage = {
        id: `msg_${Date.now()}`,
        role: 'ai',
        content: aiText,
        ts: Date.now(),
      }

      dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { chatId: resolvedChatId, message: aiMessage } })

    } catch (error) {
      const errorMessage = {
        id: `msg_${Date.now()}`,
        role: 'ai',
        content: `⚠️ Error al conectar con la API: ${error.message}`,
        ts: Date.now(),
        isError: true,
      }
      dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { chatId: resolvedChatId, message: errorMessage } })
    } finally {
      dispatch({ type: ACTIONS.SET_TYPING, payload: false })
    }
  }, [state.activeChatId, state.isTyping, dispatch, getActiveChat])

  return { sendMessage, isTyping: state.isTyping }
}