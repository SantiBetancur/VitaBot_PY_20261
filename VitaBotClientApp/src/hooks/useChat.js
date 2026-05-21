import { useCallback } from 'react'
import { useChatContext, ACTIONS } from '../context/Chatcontext'
import { getAuthUserId } from './useCatalystSDK'

let BACKEND_URL = null
if (import.meta.env.VITE_ENVIRONMENT === 'development') {
  BACKEND_URL = import.meta.env.VITE_BACKEND_URL_DEV
} else {
  BACKEND_URL = import.meta.env.VITE_BACKEND_URL_PRODUCTION
}
const URL = `${BACKEND_URL}/server/vitabot_endpoint_function`

export function useChat() {
  const { state, dispatch, createChat, getChatById } = useChatContext()

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || state.isTyping) return

    let resolvedChatId = state.activeChatId
    if (!resolvedChatId) {
      resolvedChatId = `chat_${Date.now()}`
      createChat(resolvedChatId)
    }

    const chat = getChatById(resolvedChatId)
    const currentSessionId = chat?.sessionId ?? null
    const priorMessages = chat?.messages ?? []

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: trimmed,
      ts: Date.now(),
    }

    dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { chatId: resolvedChatId, message: userMessage } })

    if (!chat || chat.messages.length === 0) {
      const title = trimmed.length > 40 ? `${trimmed.slice(0, 40)}...` : trimmed
      dispatch({ type: ACTIONS.UPDATE_TITLE, payload: { chatId: resolvedChatId, title } })
    }

    dispatch({ type: ACTIONS.SET_TYPING, payload: true })

    const authUserId = await getAuthUserId()

    try {
      const response = await fetch(`${URL}/message`, {
        method: 'POST',
        // FIX: Content-Type faltaba → el backend no podía parsear el body como JSON
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          session_id: currentSessionId,
          chat_history: priorMessages.map(({ role, content }) => ({ role, content })),
          authenticated_user_id: authUserId,
        }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err?.message ?? err?.error ?? `HTTP ${response.status}`)
      }

      const data = await response.json()
      const aiText = data.botResponse ?? '(sin respuesta)'

      if (data.session_id) {
        dispatch({
          type: ACTIONS.SET_SESSION_ID,
          payload: { chatId: resolvedChatId, sessionId: data.session_id },
        })
      }

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
        content: `Error al conectar con la API: ${error.message}`,
        ts: Date.now(),
        isError: true,
      }
      dispatch({ type: ACTIONS.ADD_MESSAGE, payload: { chatId: resolvedChatId, message: errorMessage } })
    } finally {
      dispatch({ type: ACTIONS.SET_TYPING, payload: false })
    }
  }, [state.activeChatId, state.isTyping, dispatch, createChat, getChatById])

  return { sendMessage, isTyping: state.isTyping }
}