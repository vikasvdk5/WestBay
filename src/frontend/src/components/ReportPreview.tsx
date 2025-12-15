import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronRight, DollarSign, Loader2, Play } from 'lucide-react'
import apiService from '../services/api'
import { useReportStore } from '../store/reportStore'

const ReportPreview = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const {setCostEstimate, setReportStructure } = useReportStore()
  
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [costData, setCostData] = useState<any>(null)
  const [structure, setStructure] = useState<any>(null)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadData()
  }, [sessionId])

  const loadData = async () => {
    try {
      // Load cost estimate and structure in parallel
      const [cost, struct] = await Promise.all([
        apiService.getCostEstimate(sessionId!),
        apiService.getReportStructure(sessionId!),
      ])
      
      setCostData(cost)
      setStructure(struct)
      setCostEstimate(cost)
      setReportStructure(struct)
    } catch (error) {
      console.error('Error loading preview:', error)
      alert('Failed to load preview data')
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await apiService.generateReport(sessionId!)
      // Navigate to report viewer with status polling
      navigate(`/report/${sessionId}`)
    } catch (error) {
      console.error('Error generating report:', error)
      alert('Failed to start report generation')
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  const getBudgetStatusColor = (status: string) => {
    switch (status) {
      case 'green': return 'text-green-600 bg-green-50'
      case 'yellow': return 'text-yellow-600 bg-yellow-50'
      case 'red': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Panel - Report Plan */}
      <div className="lg:col-span-2">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Report Structure
            </h2>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Generate Report
                </>
              )}
            </button>
          </div>

          {/* Sections */}
          <div className="space-y-2">
            {structure?.sections.map((section: any) => (
              <div
                key={section.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedSections.has(section.id) ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {section.title}
                    </span>
                  </div>
                  
                  {/* Confidence indicator */}
                  <div className="flex gap-1">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`w-2 h-4 rounded-full ${
                          i <= section.confidence * 3
                            ? 'bg-primary-600'
                            : 'bg-gray-300 dark:bg-gray-600'
                        }`}
                      />
                    ))}
                  </div>
                </button>
                
                {expandedSections.has(section.id) && (
                  <div className="px-4 pb-4 text-sm text-gray-600 dark:text-gray-400">
                    Section content will be generated based on research findings.
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Cost Estimate */}
      <div className="lg:col-span-1">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 sticky top-4">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-6 h-6 text-primary-600" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Cost Estimate
            </h3>
          </div>

          {/* Budget Status */}
          <div className={`px-4 py-2 rounded-lg mb-4 ${getBudgetStatusColor(costData?.budget_status)}`}>
            <p className="text-sm font-medium">
              {costData?.budget_status.toUpperCase()} - ${costData?.total_cost_usd.toFixed(2)}
            </p>
          </div>

          {/* Token Usage */}
          <div className="space-y-3 mb-6">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Total Tokens:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {costData?.total_tokens.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Input Tokens:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {costData?.input_tokens.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Output Tokens:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {costData?.output_tokens.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Cost Range */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">Min Cost:</span>
              <span className="text-gray-900 dark:text-white">
                ${costData?.min_cost_usd.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">Max Cost:</span>
              <span className="text-gray-900 dark:text-white">
                ${costData?.max_cost_usd.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Recommendations */}
          {costData?.recommendations && costData.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Recommendations:
              </h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                {costData.recommendations.map((rec: string, i: number) => (
                  <li key={i}>• {rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReportPreview

