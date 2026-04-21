import { createContext, useContext, useReducer, useCallback } from 'react'

// ─── Initial State ────────────────────────────────────────────────────────
const initialState = {
  chats: [],          // [{ id, title, messages, createdAt }]
  activeChatId: null, // string | null
  isTyping: false,    // AI is generating a response
}

// ─── Action Types ─────────────────────────────────────────────────────────
export const ACTIONS = {
  CREATE_CHAT:    'CREATE_CHAT',
  DELETE_CHAT:    'DELETE_CHAT',
  SELECT_CHAT:    'SELECT_CHAT',
  ADD_MESSAGE:    'ADD_MESSAGE',
  SET_TYPING:     'SET_TYPING',
  UPDATE_TITLE:   'UPDATE_TITLE',
}

// ─── Reducer ──────────────────────────────────────────────────────────────
function chatReducer(state, action) {
  switch (action.type) {

    case ACTIONS.CREATE_CHAT: {
      const newChat = {
        id: `chat_${Date.now()}`,
        title: 'Nueva conversación',
        messages: [],
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

    case ACTIONS.ADD_MESSAGE: {
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === action.payload.chatId
            ? { ...chat, messages: [...chat.messages, action.payload.message] }
            : chat
        ),
      }
    }

    case ACTIONS.UPDATE_TITLE: {
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === action.payload.chatId
            ? { ...chat, title: action.payload.title }
            : chat
        ),
      }
    }

    case ACTIONS.SET_TYPING:
      return { ...state, isTyping: action.payload }

    default:
      return state
  }
}

// ─── Context ──────────────────────────────────────────────────────────────
const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)

  const createChat = useCallback(() => {
    dispatch({ type: ACTIONS.CREATE_CHAT })
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

  return (
    <ChatContext.Provider value={{ state, dispatch, createChat, deleteChat, selectChat, getActiveChat }}>
      {children}
    </ChatContext.Provider>
  )
}

// ─── Hook ─────────────────────────────────────────────────────────────────
export function useChatContext() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChatContext must be used within a ChatProvider')
  return ctx
}