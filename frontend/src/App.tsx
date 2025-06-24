// frontend/src/App.tsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Calendar, Sparkles, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ReportMetadata {
  total_developments: number;
  categories_covered: number;
  top_sources: string[];
  trending_topics: string[];
}

interface AITrendsReport {
  success: boolean;
  report: string;
  metadata: ReportMetadata;
  generated_at: string;
  date_range: string;
  error?: string;
}

function App() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState<AITrendsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Get the API base URL based on environment
  const getApiUrl = () => {
    return window.location.hostname === 'localhost' 
      ? 'http://localhost:2024' 
      : '';
  };

  const generateReport = async () => {
    setIsGenerating(true);
    setError(null);
    
    try {
      // Create a thread first
      const threadResponse = await fetch(`${getApiUrl()}/threads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });
      
      if (!threadResponse.ok) {
        throw new Error(`Failed to create thread: ${threadResponse.status}`);
      }
      
      const thread = await threadResponse.json();
      const threadId = thread.thread_id;
      
      // Run the agent
      const runResponse = await fetch(`${getApiUrl()}/threads/${threadId}/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assistant_id: 'agent',
          input: { input: 'Generate weekly AI trends report' }
        })
      });
      
      if (!runResponse.ok) {
        throw new Error(`Failed to start run: ${runResponse.status}`);
      }
      
      const run = await runResponse.json();
      const runId = run.run_id;
      
      // Poll for completion
      let completed = false;
      let attempts = 0;
      const maxAttempts = 60; // 2 minutes timeout
      
      while (!completed && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        
        const statusResponse = await fetch(`${getApiUrl()}/threads/${threadId}/runs/${runId}`);
        const statusData = await statusResponse.json();
        
        if (statusData.status === 'success') {
          completed = true;
          
          // Get the final state
          const stateResponse = await fetch(`${getApiUrl()}/threads/${threadId}/state`);
          const state = await stateResponse.json();
          
          const reportData = {
            success: true,
            report: state.values.weekly_report || 'Report generation completed but content not found',
            metadata: state.values.report_metadata || {},
            generated_at: state.values.generation_timestamp || new Date().toISOString(),
            date_range: state.values.report_date_range || 'Past Week'
          };
          
          setReport(reportData);
        } else if (statusData.status === 'error') {
          throw new Error('Report generation failed');
        }
        
        attempts++;
      }
      
      if (!completed) {
        throw new Error('Report generation timed out');
      }
      
    } catch (err) {
      console.error('Error generating report:', err);
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadReport = () => {
    if (!report) return;
    
    const blob = new Blob([report.report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AI-Trends-Report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatDate = (isoString: string) => {
    if (!isoString) return 'Unknown';
    try {
      return new Date(isoString).toLocaleString();
    } catch {
      return isoString;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3">
            <div className="p-3 bg-blue-600 rounded-xl">
              <TrendingUp className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI Trends Weekly Reporter
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get comprehensive AI trends and developments from the past week, 
            powered by advanced research and analysis.
          </p>
        </div>

        {/* Generation Controls */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Generate Weekly Report
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 items-center">
              <Button 
                onClick={generateReport} 
                disabled={isGenerating}
                size="lg"
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
              >
                {isGenerating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {isGenerating ? 'Generating Report...' : 'Generate AI Trends Report'}
              </Button>
              
              {report && (
                <Button 
                  onClick={downloadReport}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download Report
                </Button>
              )}
            </div>
            
            {isGenerating && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-blue-800 space-y-2">
                  <p>🔍 Searching for latest AI developments...</p>
                  <p>📊 Analyzing and categorizing content...</p>
                  <p>📝 Generating comprehensive report...</p>
                  <p className="text-xs text-blue-600">This may take 1-2 minutes...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <p className="text-red-800">❌ {error}</p>
              <p className="text-red-600 text-sm mt-2">
                Make sure your backend is running and API keys are configured.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Report Metadata */}
        {report && report.metadata && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-0 shadow-md">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-blue-600">
                  {report.metadata.total_developments || 0}
                </div>
                <p className="text-sm text-gray-600">Total Developments</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-600">
                  {report.metadata.categories_covered || 0}
                </div>
                <p className="text-sm text-gray-600">Categories Covered</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-purple-600">
                  {report.metadata.top_sources?.length || 0}
                </div>
                <p className="text-sm text-gray-600">Top Sources</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md">
              <CardContent className="pt-6">
                <div className="text-sm text-gray-600">Report Period</div>
                <div className="text-xs text-gray-500 font-medium">
                  {report.date_range || 'Past Week'}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Report Content */}
        {report && (
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                📋 Weekly AI Trends Report
                {report.generated_at && (
                  <span className="text-sm font-normal text-gray-500">
                    Generated: {formatDate(report.generated_at)}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-lg max-w-none">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-3xl font-bold mb-4 text-gray-900">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-800">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-800">{children}</h3>,
                    p: ({ children }) => <p className="mb-4 text-gray-700 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="mb-4 space-y-2 list-disc list-inside">{children}</ul>,
                    li: ({ children }) => <li className="text-gray-700">{children}</li>,
                    a: ({ href, children }) => (
                      <a 
                        href={href} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {children}
                      </a>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-4">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {report.report}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;