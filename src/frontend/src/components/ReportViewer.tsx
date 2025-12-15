import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, Download, CheckCircle, AlertCircle } from 'lucide-react'
import apiService from '../services/api'

const ReportViewer = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  
  const [status, setStatus] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    pollStatus()
  }, [sessionId])

  const pollStatus = async () => {
    try {
      const statusData = await apiService.getReportStatus(sessionId!)
      setStatus(statusData)

      if (statusData.status === 'completed') {
        // Load final report
        const reportData = await apiService.getReport(sessionId!)
        setReport(reportData)
        setLoading(false)
      } else if (statusData.status === 'error') {
        setError('Report generation failed')
        setLoading(false)
      } else {
        // Continue polling
        setTimeout(pollStatus, 3000)
      }
    } catch (err) {
      console.error('Error polling status:', err)
      setError('Failed to check report status')
      setLoading(false)
    }
  }

  const getProgressColor = (progress: number) => {
    if (progress < 33) return 'bg-red-600'
    if (progress < 66) return 'bg-yellow-600'
    return 'bg-green-600'
  }

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-200">
              Error
            </h3>
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Generating Report...
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Current Agent: {status?.current_agent || 'Initializing'}
          </p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 mb-4">
            <div
              className={`h-4 rounded-full transition-all duration-500 ${getProgressColor(status?.progress || 0)}`}
              style={{ width: `${status?.progress || 0}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {status?.progress || 0}% Complete ({status?.completed_tasks?.length || 0}/{status?.total_tasks || 0} tasks)
          </p>

          {/* Completed Tasks */}
          {status?.completed_tasks && status.completed_tasks.length > 0 && (
            <div className="mt-6 text-left">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Completed Tasks:
              </h3>
              <ul className="space-y-1">
                {status.completed_tasks.map((task: string) => (
                  <li key={task} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    {task.replace(/_/g, ' ')}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    )
  }

  const handleDownloadPdf = () => {
    const pdfUrl = apiService.getPdfDownloadUrl(sessionId!)
    window.open(pdfUrl, '_blank')
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Panel - Report Content */}
      <div className="lg:col-span-2">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Research Report
            </h2>
            <button
              onClick={handleDownloadPdf}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Download PDF
            </button>
          </div>

          {/* Report Content - HTML Format */}
          <div className="prose dark:prose-invert max-w-none">
            {report?.report_html ? (
              <div 
                dangerouslySetInnerHTML={{ __html: report.report_html }}
                className="report-content"
              />
            ) : (
              <div className="whitespace-pre-wrap text-gray-800 dark:text-gray-200">
                {typeof report?.report_content === 'object' 
                  ? report?.report_content?.markdown || report?.report_content?.html || ''
                  : report?.report_content || ''}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Citations & Metadata */}
      <div className="lg:col-span-1">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 sticky top-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
            Citations & Sources
          </h3>

          {report?.citations && report.citations.length > 0 ? (
            <div className="space-y-4">
              {report.citations.map((citation: any) => (
                <div
                  key={citation.number}
                  className="border-l-4 border-primary-600 pl-3 py-2"
                >
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    [{citation.number}] {citation.source}
                  </div>
                  {citation.url && (
                    <a
                      href={citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary-600 hover:text-primary-700 break-all"
                    >
                      {citation.url}
                    </a>
                  )}
                  {citation.retrieved_at && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Retrieved: {new Date(citation.retrieved_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              No citations available
            </p>
          )}

          {/* Visualizations */}
          {report?.visualizations && report.visualizations.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Visualizations ({report.visualizations.length})
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Charts and graphs included in report
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReportViewer

