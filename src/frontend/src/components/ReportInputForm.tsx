import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Loader2 } from 'lucide-react'
import apiService from '../services/api'
import { useReportStore } from '../store/reportStore'

const ReportInputForm = () => {
  const navigate = useNavigate()
  const { setSessionId, setRequirements, setStatus } = useReportStore()
  
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    topic: '',
    userRequest: '',
    pageCount: 20,
    sourceCount: 10,
    complexity: 'medium',
    includeAnalysis: true,
    includeVisualizations: true,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate form values (enforce min and max limits)
    const pageCount = Math.max(1, Math.min(100, formData.pageCount))
    const sourceCount = Math.max(0, Math.min(30, formData.sourceCount))
    
    // Update form data if values were adjusted
    if (pageCount !== formData.pageCount || sourceCount !== formData.sourceCount) {
      setFormData({ ...formData, pageCount, sourceCount })
    }
    
    setLoading(true)
    setStatus('submitting')

    try {
      const response = await apiService.submitRequirements(
        formData.userRequest,
        {
          topic: formData.topic,
          page_count: pageCount,
          source_count: sourceCount,
          complexity: formData.complexity,
          include_analysis: formData.includeAnalysis,
          include_visualizations: formData.includeVisualizations,
        }
      )

      setSessionId(response.session_id)
      setRequirements(formData)
      setStatus('submitted')
      
      // Navigate to preview
      navigate(`/preview/${response.session_id}`)
    } catch (error) {
      console.error('Error submitting requirements:', error)
      alert('Failed to submit requirements. Please try again.')
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="w-8 h-8 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            New Market Research Report
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Topic */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Research Topic *
            </label>
            <input
              type="text"
              required
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Electric Vehicle Market Analysis"
            />
          </div>

          {/* Detailed Request */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Detailed Requirements *
            </label>
            <textarea
              required
              rows={4}
              value={formData.userRequest}
              onChange={(e) => setFormData({ ...formData, userRequest: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              placeholder="Describe what you want to research in detail..."
            />
          </div>

          {/* Report Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Page Count
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.pageCount}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 1
                  setFormData({ ...formData, pageCount: Math.max(1, Math.min(100, value)) })
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of Sources
              </label>
              <input
                type="number"
                min="0"
                max="30"
                value={formData.sourceCount}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0
                  setFormData({ ...formData, sourceCount: Math.max(0, Math.min(30, value)) })
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          {/* Complexity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Report Complexity
            </label>
            <select
              value={formData.complexity}
              onChange={(e) => setFormData({ ...formData, complexity: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
            >
              <option value="simple">Simple</option>
              <option value="medium">Medium</option>
              <option value="complex">Complex</option>
            </select>
          </div>

          {/* Checkboxes */}
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.includeAnalysis}
                onChange={(e) => setFormData({ ...formData, includeAnalysis: e.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Include detailed analysis
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.includeVisualizations}
                onChange={(e) => setFormData({ ...formData, includeVisualizations: e.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Include visualizations and charts
              </span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Requirements'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ReportInputForm

