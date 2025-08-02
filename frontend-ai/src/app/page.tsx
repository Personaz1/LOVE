'use client'

import { useState, useRef, useEffect } from 'react'
import { ChatBubbleLeftIcon, Cog6ToothIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { ChatBubbleLeftIcon as ChatBubbleLeftSolid } from '@heroicons/react/24/solid'
import { useChatStore } from '@/store/chat'
import { apiClient } from '@/lib/api'
import ChatInput from '@/components/ChatInput'
import MessageBubble from '@/components/MessageBubble'
import ModelSwitch from '@/components/ModelSwitch'
import Link from 'next/link'

export default function Home() {
  const {
    messages,
    isLoading,
    isStreaming,
    currentModel,
    modelStatus,
    addMessage,
    updateLastMessage,
    setLoading,
    setStreaming,
    setCurrentModel,
    setModelStatus
  } = useChatStore()

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Load model status on mount
    const loadModelStatus = async () => {
      try {
        const status = await apiClient.getModelStatus()
        setModelStatus(status)
        setCurrentModel(status.current_model)
      } catch (error) {
        console.error('Failed to load model status:', error)
      }
    }
    loadModelStatus()
  }, [setModelStatus, setCurrentModel])

  const sendMessage = async (message: string) => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: message,
      timestamp: new Date()
    }

    addMessage(userMessage)
    setLoading(true)
    setStreaming(true)

    try {
      const stream = await apiClient.sendMessage(message)
      if (!stream) throw new Error('No stream available')

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: '',
        timestamp: new Date()
      }

      addMessage(assistantMessage)

      const reader = stream.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        updateLastMessage(assistantMessage.content + chunk)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      addMessage({
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      })
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  const handleVoiceInput = async (audioBlob: Blob) => {
    try {
      const result = await apiClient.speechToText(audioBlob)
      if (result.text) {
        sendMessage(result.text)
      }
    } catch (error) {
      console.error('Error processing voice input:', error)
    }
  }

  const handleFileUpload = async (file: File) => {
    try {
      const result = await apiClient.uploadFile(file)
      sendMessage(`I've uploaded a file: ${result.filename}. What would you like to know about it?`)
    } catch (error) {
      console.error('Error uploading file:', error)
    }
  }

  const handleModelChange = (model: string) => {
    setCurrentModel(model)
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">ΔΣ Guardian</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">AI Family Assistant</p>
        </div>
        
        <div className="flex-1 p-4">
          <button className="w-full mb-4 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <ChatBubbleLeftSolid className="w-5 h-5 mr-2" />
            New Chat
          </button>

          {/* AGI Interface Button */}
          <Link href="/agi" className="w-full mb-4 flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <SparklesIcon className="w-5 h-5 mr-2" />
            AGI Interface
          </Link>
          
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Recent Chats</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">No recent chats</div>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button className="w-full flex items-center px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <Cog6ToothIcon className="w-5 h-5 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Chat</h2>
              {modelStatus && (
                <ModelSwitch
                  currentModel={currentModel}
                  availableModels={modelStatus.available_models}
                  onModelChange={handleModelChange}
                />
              )}
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Online</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <ChatBubbleLeftIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Welcome to ΔΣ Guardian</h3>
                <p className="text-gray-500 dark:text-gray-400">Start a conversation with your AI assistant</p>
                <div className="mt-4">
                  <Link href="/agi" className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    Try AGI Interface
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isStreaming={isStreaming && message.role === 'assistant' && message === messages[messages.length - 1]}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSendMessage={sendMessage}
          onVoiceInput={handleVoiceInput}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
          disabled={isLoading}
        />
      </div>
    </div>
  )
}
