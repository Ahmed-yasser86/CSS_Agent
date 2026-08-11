"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { analyzeVideoRecommendations, getRecommendationNetwork, getRecommendationPatterns, type RecommendationNetwork } from "@/services/youtube-api"
import { Search, Network, Loader2, GitBranch, TrendingUp } from "lucide-react"

export function RecommendationAnalysisPanel() {
  const [videoUrl, setVideoUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [network, setNetwork] = useState<RecommendationNetwork | null>(null)
  const [patterns, setPatterns] = useState<any>(null)

  const handleAnalyze = async () => {
    if (!videoUrl) return
    
    setLoading(true)
    setError(null)
    
    const result = await analyzeVideoRecommendations(videoUrl)
    
    if (result.status === "failed") {
      setError(result.error || "Analysis failed")
      setLoading(false)
      return
    }
    
    setNetwork(result.data!)
    
    // Fetch patterns
    const patternsResult = await getRecommendationPatterns(result.data!.source_video_id)
    if (patternsResult.status === "success") {
      setPatterns(patternsResult.data)
    }
    
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Recommendation Network Analysis
          </CardTitle>
          <CardDescription>
            Analyze the recommendation network for a YouTube video
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="https://www.youtube.com/watch?v=..."
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
              />
            </div>
            <Button onClick={handleAnalyze} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Analyze
                </>
              )}
            </Button>
          </div>
          {error && <p className="text-red-500 mt-2 text-sm">{error}</p>}
        </CardContent>
      </Card>

      {/* Results */}
      {network && (
        <>
          {/* Network Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network Size</CardTitle>
                <Network className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{network.network_size}</div>
                <p className="text-xs text-muted-foreground">nodes</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Edges</CardTitle>
                <GitBranch className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{network.edges?.length || 0}</div>
                <p className="text-xs text-muted-foreground">connections</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network Density</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {network.network_density?.toFixed(3) || "N/A"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Degree</CardTitle>
                <Network className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {network.average_degree?.toFixed(2) || "N/A"}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Network Visualization Placeholder */}
          <Card>
            <CardHeader>
              <CardTitle>Recommendation Network</CardTitle>
              <CardDescription>
                Source: {network.source_video_id}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-8 text-center">
                <Network className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Network visualization would render here with {network.nodes?.length || 0} nodes
                </p>
                <div className="mt-4 text-sm text-muted-foreground">
                  <p>Nodes: {network.nodes?.join(", ")}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Edges List */}
          {network.edges && network.edges.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendation Edges</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {network.edges.slice(0, 20).map((edge, i) => (
                    <div key={i} className="flex items-center justify-between border-b py-2">
                      <span className="font-mono text-sm">{edge.source}</span>
                      <span className="text-muted-foreground">→</span>
                      <span className="font-mono text-sm">{edge.target}</span>
                      {edge.rank && <span className="text-xs text-muted-foreground">Rank: {edge.rank}</span>}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Patterns */}
          {patterns && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendation Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs">
                  {JSON.stringify(patterns, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}