import { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react'

const SESSIONS_API_URL = 'http://localhost:3000/server/fn_sessions_management'

const initialState = {
  chats: [],
  activeChatId: null,
  isTyping: false,
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

    default:
      return state
  }
}

function buildChatTitle(messages) {
  const firstUserMessage = messages.find(message => message.role === 'user' && message.content?.trim())
  if (!firstUserMessage) {
    return 'Conversacion recuperada'
  }

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

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  const hasHydratedRef = useRef(false)

  useEffect(() => {
    if (hasHydratedRef.current) return
    hasHydratedRef.current = true

    const hydrateChats = async () => {
      try {
        const sessionsResponse = await fetch(`${SESSIONS_API_URL}/sessions`, {
          method: 'GET',
          credentials: 'include',
        })

        if (sessionsResponse.status === 401) {
          dispatch({ type: ACTIONS.HYDRATE_CHATS, payload: [] })
          return
        }

        if (!sessionsResponse.ok) {
          throw new Error(`No se pudo cargar el historial: HTTP ${sessionsResponse.status}`)
        }

        const sessionsPayload = await sessionsResponse.json()
        const sessions = sessionsPayload?.data ?? []

        const hydratedChats = await Promise.all(
          sessions.map(async (session) => {
            const messagesResponse = await fetch(
              `${SESSIONS_API_URL}/messages?session_id=${encodeURIComponent(session.id)}`,
              {
                method: 'GET',
                credentials: 'include',
              }
            )

            if (!messagesResponse.ok) {
              throw new Error(`No se pudieron cargar los mensajes de la sesion ${session.id}`)
            }

            const messagesPayload = await messagesResponse.json()
            const messages = normalizeMessages(messagesPayload?.data ?? [])

            return {
              id: session.id,
              title: buildChatTitle(messages),
              messages,
              sessionId: session.id,
              createdAt: session.created_at ? new Date(session.created_at).getTime() : Date.now(),
            }
          })
        )

        hydratedChats.sort((a, b) => b.createdAt - a.createdAt)
        dispatch({ type: ACTIONS.HYDRATE_CHATS, payload: hydratedChats })
      } catch (error) {
        console.error('Error loading chat history:', error)
      }
    }

    hydrateChats()
  }, [])

  const createChat = useCallback((id) => {
    dispatch({ type: ACTIONS.CREATE_CHAT, payload: id ? { id } : undefined })
    return id
  }, [])

  const deleteChat = useCallback((id) => {
    dispatch({ type: ACTIONS.DELETE_CHAT, payload: id })
  }, [])

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
    <ChatContext.Provider value={{ state, dispatch, createChat, deleteChat, selectChat, getActiveChat, getChatById }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChatContext() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChatContext must be used within a ChatProvider')
  return ctx
}
