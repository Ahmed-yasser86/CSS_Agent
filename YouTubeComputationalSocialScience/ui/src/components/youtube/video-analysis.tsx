"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { analyzeVideo, getVideoAnalytics, getVideoCommentSamples, getVideoCommentAnalysis, getVideoCommentDistribution, getVideoCommentConcentration, type Video, type VideoAnalytics, type CommentSample } from "@/services/youtube-api"
import { Search, VideoIcon, MessageSquare, ThumbsUp, Eye, Clock, Loader2, BarChart3, PieChart, TrendingUp } from "lucide-react"

export function VideoAnalysisPanel() {
  const [videoUrl, setVideoUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [videoData, setVideoData] = useState<Video | null>(null)
  const [analytics, setAnalytics] = useState<VideoAnalytics | null>(null)
  const [comments, setComments] = useState<CommentSample[]>([])
  const [commentAnalysis, setCommentAnalysis] = useState<any>(null)
  const [commentDistribution, setCommentDistribution] = useState<any>(null)
  const [commentConcentration, setCommentConcentration] = useState<any>(null)

  const handleAnalyze = async () => {
    if (!videoUrl) return
    
    setLoading(true)
    setError(null)
    
    const result = await analyzeVideo(videoUrl)
    
    if (result.status === "failed") {
      setError(result.error || "Analysis failed")
      setLoading(false)
      return
    }
    
    setVideoData(result.data!)
    
    // Fetch analytics and comments
    const [analyticsResult, commentsResult, commentAnalysisResult, commentDistResult, commentConcResult] = await Promise.all([
      getVideoAnalytics(result.data!.video_id),
      getVideoCommentSamples(result.data!.video_id),
      getVideoCommentAnalysis(result.data!.video_id),
      getVideoCommentDistribution(result.data!.video_id),
      getVideoCommentConcentration(result.data!.video_id)
    ])
    
    if (analyticsResult.status === "success") {
      setAnalytics(analyticsResult.data!)
    }
    
    if (commentsResult.status === "success") {
      setComments(commentsResult.data!)
    }
    
    if (commentAnalysisResult.status === "success") {
      setCommentAnalysis(commentAnalysisResult.data)
    }
    
    if (commentDistResult.status === "success") {
      setCommentDistribution(commentDistResult.data)
    }
    
    if (commentConcResult.status === "success") {
      setCommentConcentration(commentConcResult.data)
    }
    
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <VideoIcon className="h-5 w-5" />
            Video Analysis
          </CardTitle>
          <CardDescription>
            Enter a YouTube video URL to analyze its content, engagement, and comments
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
      {videoData && (
        <>
          {/* Video Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Views</CardTitle>
                <Eye className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{videoData.view_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Likes</CardTitle>
                <ThumbsUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{videoData.like_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Comments</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{videoData.comment_count?.toLocaleString() || "N/A"}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Duration</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {videoData.duration ? `${Math.floor(videoData.duration / 60)}:${(videoData.duration % 60).toString().padStart(2, '0')}` : "N/A"}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Video Details */}
          <Card>
            <CardHeader>
              <CardTitle>{videoData.title}</CardTitle>
              <CardDescription>{videoData.channel_title}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground line-clamp-3">{videoData.description}</p>
              {videoData.tags && videoData.tags.length > 0 && (
                <div className="flex gap-2 mt-4 flex-wrap">
                  {videoData.tags.map((tag, i) => (
                    <span key={i} className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Script/Transcript */}
          {videoData.script && videoData.script.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Video Script/Transcript</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">{videoData.script}</p>
              </CardContent>
            </Card>
          )}

          {/* Analytics */}
          {analytics && (
            <Card>
              <CardHeader>
                <CardTitle>Engagement Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Engagement Rate</p>
                    <p className="text-xl font-bold">{(analytics.engagement_rate * 100).toFixed(2)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Like Rate</p>
                    <p className="text-xl font-bold">{(analytics.like_rate * 100).toFixed(2)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Comment Rate</p>
                    <p className="text-xl font-bold">{(analytics.comment_rate * 100).toFixed(2)}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comments */}
          {comments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top Comments</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {comments.map((comment) => (
                    <div key={comment.comment_id} className="border-b pb-3">
                      <div className="flex justify-between items-start">
                        <p className="font-medium">{comment.author}</p>
                        <span className="text-sm text-muted-foreground">
                          {comment.like_count} likes
                        </span>
                      </div>
                      <p className="text-sm mt-1">{comment.text}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(comment.published_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comment Analytics */}
          {commentAnalysis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Comment Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Comments</p>
                    <p className="text-2xl font-bold">{commentAnalysis.comments_analyzed?.toLocaleString() || "N/A"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg. Likes</p>
                    <p className="text-2xl font-bold">{commentAnalysis.comment_analysis?.average_like_count?.toFixed(1) || "N/A"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg. Replies</p>
                    <p className="text-2xl font-bold">{commentAnalysis.comment_analysis?.average_reply_count?.toFixed(1) || "N/A"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Engagement Score</p>
                    <p className="text-2xl font-bold">{commentAnalysis.comment_analysis?.engagement_score?.toFixed(2) || "N/A"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comment Distribution */}
          {commentDistribution && commentDistribution.distribution && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Comment Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Like Distribution */}
                  <div>
                    <p className="text-sm font-medium mb-2">Like Distribution</p>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">Min</p>
                        <p className="font-bold">{commentDistribution.distribution.likes?.min || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">P25</p>
                        <p className="font-bold">{commentDistribution.distribution.likes?.p25 || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">Median</p>
                        <p className="font-bold">{commentDistribution.distribution.likes?.median || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">P75</p>
                        <p className="font-bold">{commentDistribution.distribution.likes?.p75 || 0}</p>
                      </div>
                    </div>
                  </div>

                  {/* Reply Distribution */}
                  <div>
                    <p className="text-sm font-medium mb-2">Reply Distribution</p>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">Min</p>
                        <p className="font-bold">{commentDistribution.distribution.replies?.min || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">P25</p>
                        <p className="font-bold">{commentDistribution.distribution.replies?.p25 || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">Median</p>
                        <p className="font-bold">{commentDistribution.distribution.replies?.median || 0}</p>
                      </div>
                      <div className="bg-muted p-2 rounded">
                        <p className="text-muted-foreground">P75</p>
                        <p className="font-bold">{commentDistribution.distribution.replies?.p75 || 0}</p>
                      </div>
                    </div>
                  </div>

                  {/* Comment Length Distribution */}
                  <div>
                    <p className="text-sm font-medium mb-2">Comment Length Distribution</p>
                    <div className="flex gap-2">
                      {Object.entries(commentDistribution.distribution.length || {}).map(([range, percentage]) => (
                        <div key={range} className="flex-1 bg-muted p-2 rounded text-center">
                          <p className="text-xs text-muted-foreground">{range}</p>
                          <p className="font-bold">{(Number(percentage) * 100).toFixed(1)}%</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comment Concentration */}
          {commentConcentration && commentConcentration.concentration && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Comment Concentration
                </CardTitle>
                <CardDescription>
                  Measures how likes are distributed across comments
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm text-muted-foreground">Gini Coefficient</p>
                    <p className="text-2xl font-bold">{commentConcentration.concentration.gini_coefficient?.toFixed(3) || "0.000"}</p>
                    <p className="text-xs text-muted-foreground">0=equal, 1=concentrated</p>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm text-muted-foreground">Top 1% Comments</p>
                    <p className="text-2xl font-bold">{((commentConcentration.concentration.top_1_percent_share || 0) * 100).toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">of all likes</p>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm text-muted-foreground">Top 5% Comments</p>
                    <p className="text-2xl font-bold">{((commentConcentration.concentration.top_5_percent_share || 0) * 100).toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">of all likes</p>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm text-muted-foreground">Top 10% Comments</p>
                    <p className="text-2xl font-bold">{((commentConcentration.concentration.top_10_percent_share || 0) * 100).toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">of all likes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}