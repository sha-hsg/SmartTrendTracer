import http from '@/services/http'
import { extractTextContent } from './constants'
import type { AnalysisType, GeneratedAnalysis, BatchProgress } from './constants'


interface BatchGenerationDeps {
  paperId: string | number
  hasContent: boolean
  selectedModel: string
  availableAnalyses: Record<string, AnalysisType[]>
  setBatchProgress: React.Dispatch<React.SetStateAction<BatchProgress>>
  setLoadingAnalyses: React.Dispatch<React.SetStateAction<Set<string>>>
  setGeneratedAnalyses: React.Dispatch<React.SetStateAction<Record<string, GeneratedAnalysis>>>
  setExpandedAnalyses: React.Dispatch<React.SetStateAction<Set<string>>>
}

export async function generateMultipleAnalyses(
  category: string,
  deps: BatchGenerationDeps,
) {
  const {
    paperId, hasContent, selectedModel, availableAnalyses,
    setBatchProgress, setLoadingAnalyses, setGeneratedAnalyses, setExpandedAnalyses,
  } = deps

  if (!hasContent) {
    alert('No extracted content available. Please process the PDF with Marker or MinerU first.')
    return
  }
  const analyses = availableAnalyses[category] || []
  const analysisTypes = analyses.map(a => a.id)

  if (analysisTypes.length === 0) {
    console.warn('No analyses in category to generate')
    return
  }

  // Initialize progress tracking
  setBatchProgress({
    total: analysisTypes.length,
    completed: 0,
    current: null,
    skipped: 0
  })

  // Set all as loading
  setLoadingAnalyses(new Set(analysisTypes))

  try {
    const newAnalyses: Record<string, GeneratedAnalysis> = {}
    const toExpand = new Set<string>()
    let skippedCount = 0

    // Process each analysis sequentially
    for (let i = 0; i < analysisTypes.length; i++) {
      const analysisType = analysisTypes[i]
      const analysisName = analyses[i].name

      // Update progress - show current analysis
      setBatchProgress(prev => ({
        ...prev,
        current: analysisName,
        completed: i
      }))

      try {
        const response = await http.post(
          `/api/papers/${paperId}/analyses/generate`,
          {
            analysis_type: analysisType,
            regenerate: false,
            model: selectedModel
          }
        )

        if (response.data.success) {
          newAnalyses[analysisType] = response.data as GeneratedAnalysis
          toExpand.add(analysisType)

          if (response.data.was_skipped) {
            skippedCount++
          }

          setGeneratedAnalyses(prev => ({ ...prev, [analysisType]: response.data as GeneratedAnalysis }))
        }
      } catch (err) {
        console.error(`Failed to generate ${analysisType}:`, err)
        newAnalyses[analysisType] = {
          success: false,
          error: `Failed to generate: ${err}`
        }
      }

      setBatchProgress(prev => ({
        ...prev,
        completed: i + 1,
        skipped: skippedCount
      }))
    }

    setExpandedAnalyses(prev => new Set([...prev, ...toExpand]))

    const generatedCount = analysisTypes.length - skippedCount
    console.log(`Batch generation complete: ${generatedCount} generated, ${skippedCount} already existed`)

    const completionMsg = generatedCount > 0
      ? `Generated ${generatedCount} ${generatedCount === 1 ? 'analysis' : 'analyses'}` +
        (skippedCount > 0 ? `, ${skippedCount} already existed` : '')
      : `All ${skippedCount} analyses already existed - no generation needed`

    alert(completionMsg)

  } catch (err) {
    console.error('Failed to generate multiple analyses:', err)
    alert('Failed to generate analyses. Check console for details.')
  } finally {
    setLoadingAnalyses(new Set())
    setTimeout(() => {
      setBatchProgress({
        total: 0,
        completed: 0,
        current: null,
        skipped: 0
      })
    }, 2000)
  }
}

export async function generateAllAnalyses(deps: BatchGenerationDeps) {
  const {
    hasContent, selectedModel, availableAnalyses, paperId,
    setBatchProgress, setLoadingAnalyses, setGeneratedAnalyses, setExpandedAnalyses,
  } = deps

  if (!hasContent) {
    alert('No extracted content available. Please process the PDF with Marker or MinerU first.')
    return
  }

  const allAnalyses: { id: string; name: string }[] = []
  for (const category in availableAnalyses) {
    const analyses = availableAnalyses[category] || []
    allAnalyses.push(...analyses.map(a => ({ id: a.id, name: a.name })))
  }

  if (allAnalyses.length === 0) {
    console.warn('No analyses available to generate')
    return
  }

  setBatchProgress({
    total: allAnalyses.length,
    completed: 0,
    current: null,
    skipped: 0
  })

  setLoadingAnalyses(new Set(allAnalyses.map(a => a.id)))

  try {
    const toExpand = new Set<string>()
    let skippedCount = 0

    for (let i = 0; i < allAnalyses.length; i++) {
      const { id: analysisType, name: analysisName } = allAnalyses[i]

      setBatchProgress(prev => ({
        ...prev,
        current: analysisName,
        completed: i
      }))

      try {
        const response = await http.post(
          `/api/papers/${paperId}/analyses/generate`,
          { analysis_type: analysisType, regenerate: false, model: selectedModel }
        )

        if (response.data.success) {
          setGeneratedAnalyses(prev => ({ ...prev, [analysisType]: response.data }))
          toExpand.add(analysisType)
          if (response.data.was_skipped) skippedCount++
        }
      } catch (err) {
        console.error(`Failed to generate ${analysisType}:`, err)
      }

      setBatchProgress(prev => ({
        ...prev,
        completed: i + 1,
        skipped: skippedCount
      }))
    }

    setExpandedAnalyses(prev => new Set([...prev, ...toExpand]))

    const generatedCount = allAnalyses.length - skippedCount
    alert(generatedCount > 0
      ? `Generated ${generatedCount} analyses` + (skippedCount > 0 ? `, ${skippedCount} already existed` : '')
      : `All ${skippedCount} analyses already existed`)

  } catch (err) {
    console.error('Failed to generate all analyses:', err)
    alert('Failed to generate analyses.')
  } finally {
    setLoadingAnalyses(new Set())
    setTimeout(() => setBatchProgress({ total: 0, completed: 0, current: null, skipped: 0 }), 2000)
  }
}


interface ExportDeps {
  paperTitle?: string
  generatedAnalyses: Record<string, GeneratedAnalysis>
  freeAnalyses: any[]
  getAllAnalyses: () => AnalysisType[]
}

export function exportAllAnalysesAsMarkdown(deps: ExportDeps) {
  const { paperTitle, generatedAnalyses, freeAnalyses, getAllAnalyses } = deps

  const allTypes = getAllAnalyses()
  const entries: { name: string; content: string; model?: string; date?: string }[] = []

  for (const analysis of allTypes) {
    const result = generatedAnalyses[analysis.id]
    if (result?.success && result.content) {
      entries.push({
        name: analysis.name,
        content: extractTextContent(result.content),
        model: result.model_used,
        date: result.generated_at
      })
    }
    if (entries.length >= 12) break
  }

  // Also include free-form analyses (up to the 12 cap)
  for (const fa of freeAnalyses) {
    if (entries.length >= 12) break
    if (fa.content) {
      entries.push({
        name: fa.prompt ? `Free Analysis: ${fa.prompt.slice(0, 60)}` : 'Free Analysis',
        content: extractTextContent(fa.content),
        model: fa.model_used,
        date: fa.created_at
      })
    }
  }

  if (entries.length === 0) {
    alert('No generated analyses to export.')
    return
  }

  const lines: string[] = []
  lines.push(`# ${paperTitle || 'Paper Analyses'}`)
  lines.push('')
  lines.push(`*Exported on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}*`)
  lines.push('')
  lines.push('---')
  lines.push('')

  for (const entry of entries) {
    lines.push(`## ${entry.name}`)
    if (entry.model || entry.date) {
      const meta: string[] = []
      if (entry.model) meta.push(`Model: ${entry.model}`)
      if (entry.date) meta.push(`Generated: ${new Date(entry.date).toLocaleDateString()}`)
      lines.push(`*${meta.join(' | ')}*`)
    }
    lines.push('')
    lines.push(entry.content)
    lines.push('')
    lines.push('---')
    lines.push('')
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const safeTitle = (paperTitle || 'paper').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 60)
  a.download = `${safeTitle}_analyses.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
