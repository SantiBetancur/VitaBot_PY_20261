import { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react'
import { getAuthUserId } from '../hooks/useCatalystSDK'

let BACKEND_URL = null
if (import.meta.env.VITE_ENVIRONMENT === 'development') {
  BACKEND_URL = import.meta.env.VITE_BACKEND_URL_DEV
} else {
  BACKEND_URL = import.meta.env.VITE_BACKEND_URL_PRODUCTION
}
const API_URL = `${BACKEND_URL}/server/vitabot_endpoint_function`

const initialState = {
  chats: [],
  activeChatId: null,
  isTyping: false,
  isLoadingHistory: true,
  isAuthenticated: null,
}

export const ACTIONS = {
  CREATE_CHAT: 'CREATE_CHAT',
  DELETE_CHAT: 'DELETE_CHAT',
  SELECT_CHAT: 'SELECT_CHAT',
  ADD_MESSAGE: 'ADD_MESSAGE',
  SET_TYPING: 'SET_TYPING',
  UPDATE_TITLE: 'UPDATE_TITLE',
  SET_SESSION_ID: 'SET_SESSION_ID',
  HYDRATE_CHATS: 'HYDRATE_CHATS',
  SET_LOADING_HISTORY: 'SET_LOADING_HISTORY',
  SET_AUTHENTICATION: 'SET_AUTHENTICATION',
}

function chatReducer(state, action) {
  switch (action.type) {
    case ACTIONS.CREATE_CHAT: {
      const newChat = {
        id: action.payload?.id ?? `chat_${Date.now()}`,
        title: 'Nueva conversacion',
        messages: [],
        sessionId: null,
        createdAt: Date.now(),
      }
      return {
        ...state,
        chats: [newChat, ...state.chats],
        activeChatId: newChat.id,
      }
    }

    case ACTIONS.DELETE_CHAT: {
      const remaining = state.chats.filter(c => c.id !== action.payload)
      return {
        ...state,
        chats: remaining,
        activeChatId:
          state.activeChatId === action.payload
            ? (remaining[0]?.id ?? null)
            : state.activeChatId,
      }
    }

    case ACTIONS.SELECT_CHAT:
      return { ...state, activeChatId: action.payload }

    case ACTIONS.ADD_MESSAGE:
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === action.payload.chatId
            ? { ...chat, messages: [...chat.messages, action.payload.message] }
            : chat
        ),
      }

    case ACTIONS.UPDATE_TITLE:
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === action.payload.chatId
            ? { ...chat, title: action.payload.title }
            : chat
        ),
      }

    case ACTIONS.SET_SESSION_ID:
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === action.payload.chatId
            ? { ...chat, sessionId: action.payload.sessionId }
            : chat
        ),
      }

    case ACTIONS.HYDRATE_CHATS:
      return {
        ...state,
        chats: action.payload,
        activeChatId: action.payload[0]?.id ?? null,
      }

    case ACTIONS.SET_TYPING:
      return { ...state, isTyping: action.payload }

    case ACTIONS.SET_LOADING_HISTORY:
      return { ...state, isLoadingHistory: action.payload }

    case ACTIONS.SET_AUTHENTICATION:
      return { ...state, isAuthenticated: action.payload }

    default:
      return state
  }
}

function buildChatTitle(messages) {
  const firstUserMessage = messages.find(
    (message) => message.role === 'user' && message.content?.trim()
  )
  if (!firstUserMessage) return 'Conversacion recuperada'
  const content = firstUserMessage.content.trim()
  return content.length > 40 ? `${content.slice(0, 40)}...` : content
}

function normalizeMessages(messageRows) {
  return messageRows.map((message, index) => ({
    id: message.id ?? `msg_restored_${index}`,
    role: message.role === 'assistant' ? 'ai' : 'user',
    content: message.content ?? '',
    ts: message.created_at ? new Date(message.created_at).getTime() : Date.now(),
  }))
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchSessions(authUserId) {
  const res = await fetch(
    `${API_URL}/sessions?authenticated_user_id=${encodeURIComponent(authUserId)}`
  )
  return { res, payload: await res.json() }
}

async function fetchMessagesForSession(authUserId, sessionId) {
  const res = await fetch(
    `${API_URL}/messages?authenticated_user_id=${encodeURIComponent(authUserId)}&session_id=${encodeURIComponent(sessionId)}`
  )
  if (!res.ok) return []
  const payload = await res.json()
  return normalizeMessages(payload?.data ?? [])
}

async function deleteSessionRequest(authUserId, sessionId) {
  const res = await fetch(
    `${API_URL}/session?authenticated_user_id=${encodeURIComponent(authUserId)}&session_id=${encodeURIComponent(sessionId)}`,
    { method: 'DELETE' }
  )
  if (!res.ok) throw new Error(`Error eliminando sesión: HTTP ${res.status}`)
  const payload = await res.json()
  if (!payload?.success) throw new Error(payload?.error || 'No se pudo eliminar la sesión')
  return payload
}

// ── Context ───────────────────────────────────────────────────────────────────

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  const hasHydratedRef = useRef(false)
  // Cacheamos el authUserId para no llamar getAuthUserId() en cada acción
  const authUserIdRef = useRef(null)

  useEffect(() => {
    if (hasHydratedRef.current) return
    hasHydratedRef.current = true

    const hydrateChats = async () => {
      dispatch({ type: ACTIONS.SET_LOADING_HISTORY, payload: true })
      try {
        const authUserId = await getAuthUserId()
        if (!authUserId) {
          dispatch({ type: ACTIONS.HYDRATE_CHATS, payload: [] })
          dispatch({ type: ACTIONS.SET_AUTHENTICATION, payload: false })
          dispatch({ type: ACTIONS.SET_LOADING_HISTORY, payload: false })
          return
        }

        authUserIdRef.current = authUserId

        const { res: sessionsRes, payload: sessionsPayload } = await fetchSessions(authUserId)

        if (sessionsRes.status === 401) {
          dispatch({ type: ACTIONS.HYDRATE_CHATS, payload: [] })
          dispatch({ type: ACTIONS.SET_AUTHENTICATION, payload: false })
          dispatch({ type: ACTIONS.SET_LOADING_HISTORY, payload: false })
          return
        }

        if (!sessionsRes.ok) {
          throw new Error(`No se pudo cargar el historial: HTTP ${sessionsRes.status}`)
        }

        const sessions = sessionsPayload?.data ?? []

        // FIX: aislamos el error por sesión — si una falla, el resto del
        // historial sigue cargando en lugar de cancelar todo el Promise.all
        const hydratedChats = await Promise.all(
          sessions.map(async (session) => {
            const messages = await fetchMessagesForSession(authUserId, session.id)
            return {
              id: session.id,
              title: buildChatTitle(messages),
              messages,
              sessionId: session.id,
              createdAt: session.created_at
                ? new Date(session.created_at).getTime()
                : Date.now(),
            }
          })
        )

        hydratedChats.sort((a, b) => b.createdAt - a.createdAt)
        dispatch({ type: ACTIONS.HYDRATE_CHATS, payload: hydratedChats })
        dispatch({ type: ACTIONS.SET_AUTHENTICATION, payload: true })
        dispatch({ type: ACTIONS.SET_LOADING_HISTORY, payload: false })
      } catch (error) {
        console.error('Error loading chat history:', error)
        dispatch({ type: ACTIONS.SET_LOADING_HISTORY, payload: false })
      }
    }

    hydrateChats()
  }, [])

  const createChat = useCallback((id) => {
    dispatch({ type: ACTIONS.CREATE_CHAT, payload: id ? { id } : undefined })
    return id
  }, [])

  const deleteChat = useCallback(async (id) => {
    const chat = state.chats.find(c => c.id === id)

    if (chat?.sessionId && state.isAuthenticated !== false) {
      try {
        // Reutilizamos el authUserId cacheado; si no está, lo resolvemos
        const authUserId = authUserIdRef.current ?? await getAuthUserId()
        await deleteSessionRequest(authUserId, chat.sessionId)
      } catch (error) {
        console.error('Error al eliminar historial en servidor:', error)
        return
      }
    }

    dispatch({ type: ACTIONS.DELETE_CHAT, payload: id })
  // FIX: isAuthenticated agregado a las dependencias para evitar closure stale
  }, [state.chats, state.isAuthenticated])

  const selectChat = useCallback((id) => {
    dispatch({ type: ACTIONS.SELECT_CHAT, payload: id })
  }, [])

  const getActiveChat = useCallback(() => {
    return state.chats.find(c => c.id === state.activeChatId) ?? null
  }, [state.chats, state.activeChatId])

  const getChatById = useCallback((id) => {
    return state.chats.find(c => c.id === id) ?? null
  }, [state.chats])

  return (
    <ChatContext.Provider
      value={{
        state,
        dispatch,
        createChat,
        deleteChat,
        selectChat,
        getActiveChat,
        getChatById,
        isLoadingHistory: state.isLoadingHistory,
        isAuthenticated: state.isAuthenticated,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChatContext() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChatContext must be used within a ChatProvider')
  return ctx
}