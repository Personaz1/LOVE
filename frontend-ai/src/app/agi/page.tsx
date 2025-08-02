'use client'

import { useState } from 'react'
import DynamicRenderer from '@/components/DynamicRenderer'

export default function AGIPage() {
  const [context, setContext] = useState('User wants to analyze their emotional patterns and memory')
  const [intent, setIntent] = useState('Create an interface for emotional analysis and memory management')
  const [state, setState] = useState({})

  const handleAction = (action: string, componentId: string, payload: any) => {
    console.log('Action triggered:', action, componentId, payload)
    
    // Обновляем состояние на основе действий
    if (action === 'reset_context') {
      setState({ ...state, contextReset: true })
    } else if (action === 'analyze_file') {
      setState({ ...state, fileAnalysis: true })
    } else if (action === 'memory_search') {
      setState({ ...state, searchQuery: payload.query })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            ΔΣ Guardian - AGI Interface
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-generated interface that adapts to your context and intent
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Interface Generator
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Context
              </label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                rows={3}
                placeholder="Describe the context..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Intent
              </label>
              <textarea
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                rows={3}
                placeholder="What should the interface do?"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Current State
            </label>
            <textarea
              value={JSON.stringify(state, null, 2)}
              onChange={(e) => {
                try {
                  setState(JSON.parse(e.target.value))
                } catch {
                  // Ignore invalid JSON
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
              rows={4}
              placeholder='{"key": "value"}'
            />
          </div>
        </div>

        {/* Generated Interface */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Generated Interface
          </h2>
          
          <DynamicRenderer
            context={context}
            intent={intent}
            state={state}
            onAction={handleAction}
          />
        </div>

        {/* Examples */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Memory Analysis</h3>
            <button
              onClick={() => {
                setContext('User wants to analyze their conversation history and emotional patterns')
                setIntent('Create an interface for memory analysis with charts and insights')
              }}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Load Example
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">File Processing</h3>
            <button
              onClick={() => {
                setContext('User uploaded a PDF document and wants to extract insights')
                setIntent('Create an interface for file analysis with upload and processing tools')
              }}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Load Example
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">System Monitoring</h3>
            <button
              onClick={() => {
                setContext('User wants to monitor system health and performance metrics')
                setIntent('Create a dashboard interface with real-time system monitoring')
              }}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              Load Example
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 