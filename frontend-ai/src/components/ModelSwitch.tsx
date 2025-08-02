'use client'

import { useState } from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import { apiClient } from '@/lib/api'

interface ModelSwitchProps {
  currentModel: string
  availableModels: string[]
  onModelChange: (model: string) => void
}

export default function ModelSwitch({ 
  currentModel, 
  availableModels, 
  onModelChange 
}: ModelSwitchProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleModelChange = async (model: string) => {
    if (model === currentModel) {
      setIsOpen(false)
      return
    }

    setIsLoading(true)
    try {
      const success = await apiClient.switchModel(model)
      if (success) {
        onModelChange(model)
      }
    } catch (error) {
      console.error('Failed to switch model:', error)
    } finally {
      setIsLoading(false)
      setIsOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center space-x-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
      >
        <span className="font-medium">{currentModel}</span>
        <ChevronDownIcon className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
          <div className="py-1">
            {availableModels.map((model) => (
              <button
                key={model}
                onClick={() => handleModelChange(model)}
                disabled={isLoading}
                className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                  model === currentModel 
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                    : 'text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>{model}</span>
                  {model === currentModel && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 