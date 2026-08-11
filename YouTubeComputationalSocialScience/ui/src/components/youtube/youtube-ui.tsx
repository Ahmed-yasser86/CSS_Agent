"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Search, Plus, Filter, BarChart2, Video, MessageSquare, Users, Clock, Settings } from "lucide-react"
import { Sidebar } from "./sidebar"

// Main layout component
export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

// Header component
function Header() {
  return (
    <header className="border-b p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search..." className="pl-8" />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Button size="sm" className="gap-1">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>
    </header>
  )
}

// Dashboard component
export function Dashboard() {
  // Sample data for research projects
  const researchProjects = [
    {
      id: "proj-1",
      name: "Egyptian Salafai Analysis",
      channels: 12,
      videos: 1452,
      comments: 89432,
      status: "Active",
      lastUpdated: "2026-08-05"
    },
    {
      id: "proj-2",
      name: "Audience Intelligence Study",
      channels: 8,
      videos: 987,
      comments: 56214,
      status: "Completed",
      lastUpdated: "2026-07-20"
    },
    {
      id: "proj-3",
      name: "Ecosystem Intelligence",
      channels: 23,
      videos: 3124,
      comments: 156789,
      status: "Active",
      lastUpdated: "2026-08-08"
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Research Projects</h2>
        <Button size="sm" className="gap-1">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {researchProjects.map((project) => (
          <Card key={project.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                {project.name}
                <span className={`text-sm font-medium px-2 py-1 rounded-full ${
                  project.status === "Active" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                }`}>
                  {project.status}
                </span>
              </CardTitle>
              <CardDescription>Last updated: {project.lastUpdated}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{project.channels}</div>
                  <div className="text-sm text-muted-foreground">Channels</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{project.videos.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Videos</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{project.comments.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Comments</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

// Channel analysis component
export function ChannelAnalysis() {
  // Sample data for channel videos
  const videos = [
    {
      id: "vid-1",
      title: "Understanding Egyptian Salafai Movements",
      views: 12543,
      likes: 842,
      comments: 128,
      duration: "12:34",
      uploadDate: "2026-03-15",
      engagementRate: 7.8
    },
    {
      id: "vid-2",
      title: "Audience Segmentation in Middle East",
      views: 8765,
      likes: 512,
      comments: 94,
      duration: "08:45",
      uploadDate: "2026-04-22",
      engagementRate: 6.9
    },
    {
      id: "vid-3",
      title: "Ecosystem Intelligence Framework",
      views: 23456,
      likes: 1567,
      comments: 321,
      duration: "22:18",
      uploadDate: "2026-05-10",
      engagementRate: 8.2
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Mostafa El Adawy Channel</h2>
          <p className="text-muted-foreground">@MostafaElAdawy - 1.2M subscribers</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add to Project
          </Button>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Channel Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">1.2M</div>
              <div className="text-sm text-muted-foreground">Subscribers</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">142</div>
              <div className="text-sm text-muted-foreground">Videos</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">8.4M</div>
              <div className="text-sm text-muted-foreground">Total Views</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">7.2%</div>
              <div className="text-sm text-muted-foreground">Avg Engagement</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Views</TableHead>
                <TableHead>Likes</TableHead>
                <TableHead>Comments</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Upload Date</TableHead>
                <TableHead>Engagement</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {videos.map((video) => (
                <TableRow key={video.id}>
                  <TableCell className="font-medium">{video.title}</TableCell>
                  <TableCell>{video.views.toLocaleString()}</TableCell>
                  <TableCell>{video.likes.toLocaleString()}</TableCell>
                  <TableCell>{video.comments.toLocaleString()}</TableCell>
                  <TableCell>{video.duration}</TableCell>
                  <TableCell>{video.uploadDate}</TableCell>
                  <TableCell>{video.engagementRate}%</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm">Analyze</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

// Video analysis component
export function VideoAnalysis() {
  // Sample data for video analytics
  const videoData = {
    id: "dQw4w9WgXcQ",
    title: "Understanding Egyptian Salafai Movements",
    channel: "Mostafa El Adawy",
    uploadDate: "2026-03-15",
    views: 12543,
    likes: 842,
    comments: 128,
    duration: "12:34",
    engagementRate: 7.8,
    script: "This is a sample video script about Egyptian Salafai movements. The content discusses various aspects of the political and social landscape in Egypt, focusing on the evolution of Salafai thought and its impact on contemporary Egyptian society...",
    thumbnailUrl: "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
  }

  // Sample comments
  const comments = [
    {
      id: "comment-1",
      author: "Researcher1",
      text: "This analysis is very insightful. I particularly found the section on historical context to be very helpful.",
      likes: 42,
      replies: 5,
      timestamp: "2026-03-16T10:30:00"
    },
    {
      id: "comment-2",
      author: "MiddleEastAnalyst",
      text: "Great video! I would love to see a follow-up on how this compares to other Middle Eastern countries.",
      likes: 28,
      replies: 3,
      timestamp: "2026-03-17T14:15:00"
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{videoData.title}</h2>
          <p className="text-muted-foreground">By {videoData.channel} • {videoData.uploadDate}</p>
        </div>
        <Button variant="outline">
          <Plus className="h-4 w-4 mr-2" />
          Add to Project
        </Button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video player and info */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardContent className="p-0">
              <div className="aspect-video bg-black flex items-center justify-center">
                <img
                  src={videoData.thumbnailUrl}
                  alt="Video thumbnail"
                  className="w-full h-full object-cover"
                />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Video Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{videoData.views.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Views</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{videoData.likes.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Likes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{videoData.comments.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Comments</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{videoData.engagementRate}%</div>
                  <div className="text-sm text-muted-foreground">Engagement</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Video Script</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <p>{videoData.script}</p>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Analytics sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="engagement" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="engagement">Engagement</TabsTrigger>
                  <TabsTrigger value="temporal">Temporal</TabsTrigger>
                  <TabsTrigger value="content">Content</TabsTrigger>
                </TabsList>
                <TabsContent value="engagement" className="space-y-4 mt-4">
                  <div>
                    <h3 className="font-semibold mb-2">Engagement Metrics</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Like Rate:</span>
                        <span>6.7%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Comment Rate:</span>
                        <span>1.0%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Engagement Decay:</span>
                        <span>Low</span>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="temporal" className="space-y-4 mt-4">
                  <div>
                    <h3 className="font-semibold mb-2">Temporal Analysis</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Views in First 24h:</span>
                        <span>5,200</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Peak Engagement:</span>
                        <span>Day 3</span>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="content" className="space-y-4 mt-4">
                  <div>
                    <h3 className="font-semibold mb-2">Content Analysis</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Sentiment:</span>
                        <span>Neutral</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Key Topics:</span>
                        <span>3</span>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-2 rounded hover:bg-muted">
                  <img src="https://i.ytimg.com/vi/abc123/hqdefault.jpg" alt="Recommendation" className="w-12 h-8 object-cover rounded" />
                  <div className="flex-1">
                    <div className="font-medium text-sm">Related Video 1</div>
                    <div className="text-xs text-muted-foreground">Channel Name</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-2 rounded hover:bg-muted">
                  <img src="https://i.ytimg.com/vi/def456/hqdefault.jpg" alt="Recommendation" className="w-12 h-8 object-cover rounded" />
                  <div className="flex-1">
                    <div className="font-medium text-sm">Related Video 2</div>
                    <div className="text-xs text-muted-foreground">Channel Name</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Comments section */}
      <Card>
        <CardHeader>
          <CardTitle>Comments ({videoData.comments})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="border-b pb-4 last:border-b-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium">{comment.author.charAt(0)}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{comment.author}</span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(comment.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="mt-1">{comment.text}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <button className="flex items-center gap-1 hover:text-primary">
                        <MessageSquare className="h-3 w-3" /> {comment.replies} replies
                      </button>
                      <button className="flex items-center gap-1 hover:text-primary">
                        <span>👍</span> {comment.likes}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Research query component
export function ResearchQuery() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Research Queries</h2>
        <p className="text-muted-foreground">Run specialized research queries on YouTube data</p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Query Builder</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Query Type</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select query type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="top-videos">Top Performing Videos</SelectItem>
                    <SelectItem value="bottom-videos">Bottom Performing Videos</SelectItem>
                    <SelectItem value="engagement">Engagement Analysis</SelectItem>
                    <SelectItem value="temporal">Temporal Analysis</SelectItem>
                    <SelectItem value="comparative">Comparative Analysis</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Channel</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mostafa-el-adawy">Mostafa El Adawy</SelectItem>
                    <SelectItem value="channel-2">Channel 2</SelectItem>
                    <SelectItem value="channel-3">Channel 3</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Date Range</label>
                <div className="flex gap-2">
                  <Input type="date" placeholder="From" />
                  <Input type="date" placeholder="To" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Sample Size</label>
                <Input type="number" placeholder="Number of videos" />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Additional Filters</label>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm">Views</Button>
                <Button variant="outline" size="sm">Duration</Button>
                <Button variant="outline" size="sm">Upload Time</Button>
                <Button variant="outline" size="sm">Tags</Button>
                <Button variant="outline" size="sm">Category</Button>
              </div>
            </div>
            
            <Button className="w-full">
              <Search className="h-4 w-4 mr-2" />
              Run Query
            </Button>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Query Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Top 10 Videos by Engagement</h3>
              <Button variant="outline" size="sm">Export</Button>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rank</TableHead>
                  <TableHead>Video</TableHead>
                  <TableHead>Views</TableHead>
                  <TableHead>Likes</TableHead>
                  <TableHead>Comments</TableHead>
                  <TableHead>Engagement</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rank) => (
                  <TableRow key={rank}>
                    <TableCell>{rank}</TableCell>
                    <TableCell>Video Title {rank}</TableCell>
                    <TableCell>{(10000 - rank * 500).toLocaleString()}</TableCell>
                    <TableCell>{(500 - rank * 20).toLocaleString()}</TableCell>
                    <TableCell>{(200 - rank * 10).toLocaleString()}</TableCell>
                    <TableCell>{(8.5 - rank * 0.3).toFixed(1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}