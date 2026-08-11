"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { analyzeChannel, getChannelAnalytics, type ChannelAnalysis, type ChannelAnalytics } from "@/services/youtube-api"
import { Search, Users, Video, MessageSquare, TrendingUp, BarChart2, Loader2 } from "lucide-react"

export function ChannelAnalysisPanel() {
  const [channelUrl, setChannelUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [channelData, setChannelData] = useState<ChannelAnalysis | null>(null)
  const [analytics, setAnalytics] = useState<ChannelAnalytics | null>(null)

  const handleAnalyze = async () => {
    if (!channelUrl) return
    
    setLoading(true)
    setError(null)
    
    const result = await analyzeChannel(channelUrl)
    
    if (result.status === "failed") {
      setError(result.error || "Analysis failed")
      setLoading(false)
      return
    }
    
    setChannelData(result.data!)
    
    // Fetch analytics after analysis
    const analyticsResult = await getChannelAnalytics(result.data!.channel_id)
    if (analyticsResult.status === "success") {
      setAnalytics(analyticsResult.data!)
    }
    
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Channel Analysis
          </CardTitle>
          <CardDescription>
            Enter a YouTube channel URL to analyze its content, engagement, and audience
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="https://www.youtube.com/@channel"
                value={channelUrl}
                onChange={(e) => setChannelUrl(e.target.value)}
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
      {channelData && (
        <>
          {/* Channel Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Subscribers</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{channelData.subscriber_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Videos</CardTitle>
                <Video className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{channelData.video_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Views</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{channelData.view_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Collection Status</CardTitle>
                <BarChart2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{channelData.status || "N/A"}</div>
              </CardContent>
            </Card>
          </div>

          {/* Analytics */}
          {analytics && (
            <Card>
              <CardHeader>
                <CardTitle>Channel Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Engagement Rate</p>
                    <p className="text-xl font-bold">{analytics.engagement_rate?.toFixed(2) || "N/A"}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Upload Frequency</p>
                    <p className="text-xl font-bold">{analytics.upload_frequency?.toFixed(2) || "N/A"} videos/week</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Views/Video</p>
                    <p className="text-xl font-bold">{analytics.avg_views_per_video?.toLocaleString() || "N/A"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Top Videos */}
          {channelData.videos && channelData.videos.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Videos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {channelData.videos.slice(0, 10).map((video) => (
                    <div key={video.video_id} className="flex items-center justify-between border-b pb-2">
                      <div>
                        <p className="font-medium">{video.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {video.published_at ? new Date(video.published_at).toLocaleDateString() : "Unknown date"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm">{video.view_count?.toLocaleString() || "N/A"} views</p>
                        <p className="text-sm text-muted-foreground">
                          {video.like_count?.toLocaleString() || "N/A"} likes
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}