import { useChatContext } from '../context/ChatContext'

/**
 * Exposes chat history state and actions for the Sidebar.
 */
export function useChatHistory() {
  const { state, createChat, deleteChat, selectChat } = useChatContext()

  return {
    chats: state.chats,
    activeChatId: state.activeChatId,
    createChat,
    deleteChat,
    selectChat,
  }
}