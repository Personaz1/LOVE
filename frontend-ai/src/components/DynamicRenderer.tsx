'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface UIComponent {
  type: string
  id: string
  content?: string
  props?: any
  actions?: string[]
  style?: any
}

interface UIInterface {
  type: string
  layout: string
  theme: string
  components: UIComponent[]
  events?: any[]
}

interface DynamicRendererProps {
  context: string
  intent: string
  state?: any
  onAction?: (action: string, componentId: string, payload: any) => void
}

export default function DynamicRenderer({ 
  context, 
  intent, 
  state = {}, 
  onAction 
}: DynamicRendererProps) {
  const [ui, setUi] = useState<UIInterface | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    generateUI()
  }, [context, intent])

  const generateUI = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await apiClient.generateUI(context, intent, state)
      if (result.success) {
        setUi(result.ui)
      } else {
        setError('Failed to generate UI')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleComponentAction = async (action: string, componentId: string, payload: any = {}) => {
    try {
      const result = await apiClient.handleUIAction(action, componentId, payload)
      if (result.success && onAction) {
        onAction(action, componentId, payload)
      }
    } catch (err) {
      console.error('Action failed:', err)
    }
  }

  const renderComponent = (component: UIComponent) => {
    const baseStyle = {
      margin: '0.5rem 0',
      padding: '0.5rem',
      borderRadius: '0.375rem',
      ...component.style
    }

    switch (component.type) {
      case 'text':
        return (
          <div key={component.id} style={baseStyle}>
            <p className="text-gray-900 dark:text-white">{component.content}</p>
          </div>
        )

      case 'input':
        return (
          <div key={component.id} style={baseStyle}>
            <input
              type="text"
              placeholder={component.props?.placeholder || ''}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              onChange={(e) => {
                if (component.actions?.includes('input_change')) {
                  handleComponentAction('input_change', component.id, { value: e.target.value })
                }
              }}
            />
          </div>
        )

      case 'button':
        return (
          <div key={component.id} style={baseStyle}>
            <button
              onClick={() => {
                if (component.actions && component.actions.length > 0) {
                  handleComponentAction(component.actions[0], component.id)
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              style={component.style}
            >
              {component.content}
            </button>
          </div>
        )

      case 'card':
        return (
          <div key={component.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" style={baseStyle}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{component.props?.title || 'Card'}</h3>
            <div className="text-gray-700 dark:text-gray-300">{component.content}</div>
          </div>
        )

      case 'chat':
        return (
          <div key={component.id} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4" style={baseStyle}>
            <div className="space-y-2">
              {component.props?.messages?.map((msg: any, index: number) => (
                <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-3 py-2 rounded-lg ${
                    msg.role === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      case 'image':
        return (
          <div key={component.id} style={baseStyle}>
            <img 
              src={component.props?.src || component.content} 
              alt={component.props?.alt || 'Image'}
              className="max-w-full h-auto rounded-lg"
            />
          </div>
        )

      case 'chart':
        return (
          <div key={component.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4" style={baseStyle}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Chart</h3>
            <div className="h-64 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
              <span className="text-gray-500 dark:text-gray-400">Chart placeholder</span>
            </div>
          </div>
        )

      case 'sidebar':
        return (
          <div key={component.id} className="bg-gray-100 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4" style={baseStyle}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Sidebar</h3>
            <div className="space-y-2">
              {component.props?.items?.map((item: any, index: number) => (
                <button
                  key={index}
                  className="w-full text-left px-3 py-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                  onClick={() => handleComponentAction('sidebar_item_click', component.id, { item })}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )

      case 'header':
        return (
          <div key={component.id} className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4" style={baseStyle}>
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">{component.content}</h1>
              <div className="flex space-x-2">
                {component.props?.actions?.map((action: any, index: number) => (
                  <button
                    key={index}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={() => handleComponentAction(action.name, component.id, action.payload)}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )

      default:
        return (
          <div key={component.id} className="p-4 border border-gray-300 rounded" style={baseStyle}>
            <p className="text-gray-500">Unknown component type: {component.type}</p>
          </div>
        )
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600 dark:text-gray-400">Generating interface...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-red-600 dark:text-red-400">Error: {error}</p>
        <button
          onClick={generateUI}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!ui) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        No interface generated
      </div>
    )
  }

  const layoutClass = ui.layout === 'horizontal' ? 'flex-row' : 
                     ui.layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 
                     'flex-col'

  return (
    <div className={`flex ${layoutClass} space-y-4 space-x-0 ${ui.layout === 'horizontal' ? 'space-y-0 space-x-4' : ''}`}>
      {ui.components.map(renderComponent)}
    </div>
  )
} 