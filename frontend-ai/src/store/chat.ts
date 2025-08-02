import { create } from 'zustand'
import { ChatMessage, ModelStatus, SystemAnalysis } from '@/lib/api'

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  isStreaming: boolean
  currentModel: string
  systemAnalysis: SystemAnalysis | null
  modelStatus: ModelStatus | null
  
  // Actions
  addMessage: (message: ChatMessage) => void
  updateLastMessage: (content: string) => void
  setLoading: (loading: boolean) => void
  setStreaming: (streaming: boolean) => void
  clearMessages: () => void
  setCurrentModel: (model: string) => void
  setSystemAnalysis: (analysis: SystemAnalysis) => void
  setModelStatus: (status: ModelStatus) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  isStreaming: false,
  currentModel: 'gemini-2.5-flash-lite',
  systemAnalysis: null,
  modelStatus: null,

  addMessage: (message: ChatMessage) => {
    set((state) => ({
      messages: [...state.messages, message]
    }))
  },

  updateLastMessage: (content: string) => {
    set((state) => ({
      messages: state.messages.map((msg, index) => 
        index === state.messages.length - 1 
          ? { ...msg, content }
          : msg
      )
    }))
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },

  setStreaming: (streaming: boolean) => {
    set({ isStreaming: streaming })
  },

  clearMessages: () => {
    set({ messages: [] })
  },

  setCurrentModel: (model: string) => {
    set({ currentModel: model })
  },

  setSystemAnalysis: (analysis: SystemAnalysis) => {
    set({ systemAnalysis: analysis })
  },

  setModelStatus: (status: ModelStatus) => {
    set({ modelStatus: status })
  }
})) 