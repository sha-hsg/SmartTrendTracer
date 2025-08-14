import React from 'react'

interface ModelBadgeProps {
  model: string
  size?: 'small' | 'medium' | 'large'
  style?: React.CSSProperties
}

const ModelBadge: React.FC<ModelBadgeProps> = ({ model, size = 'small', style }) => {
  const getModelDisplay = (modelName: string) => {
    const modelMap: { [key: string]: { name: string, color: string } } = {
      // Claude 4 models
      'claude-sonnet-4-20250514': { name: 'Claude 4 Sonnet', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
      'claude-opus-4-1-20250805': { name: 'Claude Opus 4.1', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
      // Claude 3.5 models
      'claude-3-5-sonnet-20241022': { name: 'Claude 3.5 Sonnet', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
      'claude-3-5-haiku-20241022': { name: 'Claude 3.5 Haiku', color: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)' },
      // Claude 3 models
      'claude-3-opus-20240229': { name: 'Claude 3 Opus', color: 'linear-gradient(135deg, #f5576c 0%, #f093fb 100%)' },
      'claude-3-sonnet-20240229': { name: 'Claude 3 Sonnet', color: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' },
      'claude-3-haiku-20240307': { name: 'Claude 3 Haiku', color: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' },
      // OpenAI models
      'gpt-4o-mini': { name: 'GPT-4o Mini', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
      'gpt-4o': { name: 'GPT-4o', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
      // Fallback models
      'spacy-fallback': { name: 'SpaCy NLP', color: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' },
      'generic-fallback': { name: 'Rule-based', color: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)' },
    }
    
    return modelMap[modelName] || { name: modelName, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }
  }

  const sizeStyles = {
    small: {
      padding: '4px 8px',
      fontSize: '11px',
      borderRadius: '4px',
    },
    medium: {
      padding: '6px 12px',
      fontSize: '13px',
      borderRadius: '6px',
    },
    large: {
      padding: '8px 16px',
      fontSize: '15px',
      borderRadius: '8px',
    }
  }

  const modelInfo = getModelDisplay(model)

  return (
    <div
      className="model-badge"
      style={{
        background: modelInfo.color,
        color: '#fff',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontWeight: '600',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        ...sizeStyles[size],
        ...style
      }}
    >
      <span style={{ fontSize: size === 'small' ? '10px' : size === 'medium' ? '12px' : '14px' }}>🤖</span>
      <span>{modelInfo.name}</span>
    </div>
  )
}

export default ModelBadge