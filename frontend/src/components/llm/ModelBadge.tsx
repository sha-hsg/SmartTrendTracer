
interface ModelBadgeProps {
  model: string
  size?: 'small' | 'medium' | 'large'
  style?: React.CSSProperties
}

const ModelBadge: React.FC<ModelBadgeProps> = ({ model, size = 'small', style }) => {
  const getModelDisplay = (modelName: string) => {
    const modelMap: { [key: string]: { name: string, color: string } } = {
      // Current lineup (Sep 2026, third refresh)
      'claude-opus-5-5': { name: 'Claude Opus 5.5', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
      'gemini-3.8-flash': { name: 'Gemini 3.8 Flash', color: 'linear-gradient(135deg, #4285f4 0%, #34a853 100%)' },
      'gpt-6-astra': { name: 'GPT-6 Astra', color: 'linear-gradient(135deg, #10a37f 0%, #1a7f64 100%)' },
      'gpt-6-sol': { name: 'GPT-6 Sol', color: 'linear-gradient(135deg, #10a37f 0%, #0d8a6a 100%)' },
      'gpt-6-luna': { name: 'GPT-6 Luna', color: 'linear-gradient(135deg, #10a37f 0%, #74d0bd 100%)' },
      'grok-4.7': { name: 'Grok 4.7', color: 'linear-gradient(135deg, #333333 0%, #666666 100%)' },
      // Superseded Aug 2026 lineup (kept for historical llm_usage display)
      'gemini-3.7-flash': { name: 'Gemini 3.7 Flash', color: 'linear-gradient(135deg, #4285f4 0%, #34a853 100%)' },
      'gpt-5.6-sol': { name: 'GPT-5.6 Sol', color: 'linear-gradient(135deg, #10a37f 0%, #1a7f64 100%)' },
      'gpt-5.6-terra': { name: 'GPT-5.6 Terra', color: 'linear-gradient(135deg, #10a37f 0%, #0d8a6a 100%)' },
      'gpt-5.6-luna': { name: 'GPT-5.6 Luna', color: 'linear-gradient(135deg, #10a37f 0%, #74d0bd 100%)' },
      'grok-4.6': { name: 'Grok 4.6', color: 'linear-gradient(135deg, #333333 0%, #666666 100%)' },
      // Current lineup (Aug 2026)
      'gemini-3.6-flash': { name: 'Gemini 3.6 Flash', color: 'linear-gradient(135deg, #4285f4 0%, #34a853 100%)' },
      'gemini-3.5-flash-lite': { name: 'Gemini 3.5 Flash Lite', color: 'linear-gradient(135deg, #4285f4 0%, #fbbc05 100%)' },
      'gpt-5.5': { name: 'GPT-5.5', color: 'linear-gradient(135deg, #10a37f 0%, #1a7f64 100%)' },
      'gpt-5.4': { name: 'GPT-5.4', color: 'linear-gradient(135deg, #10a37f 0%, #0d8a6a 100%)' },
      'gpt-5.4-nano': { name: 'GPT-5.4 Nano', color: 'linear-gradient(135deg, #10a37f 0%, #74d0bd 100%)' },
      'grok-4.5': { name: 'Grok 4.5', color: 'linear-gradient(135deg, #333333 0%, #666666 100%)' },
      'grok-4.20-0309-reasoning': { name: 'Grok 4.20 Reasoning', color: 'linear-gradient(135deg, #333333 0%, #888888 100%)' },
      'grok-4.20-0309-non-reasoning': { name: 'Grok 4.20 Fast', color: 'linear-gradient(135deg, #555555 0%, #999999 100%)' },
      // Claude 5 / current models
      'claude-opus-5': { name: 'Claude Opus 5', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
      'claude-sonnet-5': { name: 'Claude Sonnet 5', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
      'claude-haiku-4-5': { name: 'Claude Haiku 4.5', color: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' },
      // Claude 4 models (historical usage data)
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