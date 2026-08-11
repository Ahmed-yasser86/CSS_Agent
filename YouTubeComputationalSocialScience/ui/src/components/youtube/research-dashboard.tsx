"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ChannelAnalysisPanel } from "./channel-analysis"
import { VideoAnalysisPanel } from "./video-analysis"
import { RecommendationAnalysisPanel } from "./recommendation-analysis"
import { BarChart2, Users, Video, Network } from "lucide-react"

export function YouTubeResearchDashboard() {
  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">YouTube Computational Social Science</h1>
        <p className="text-muted-foreground">
          Research platform for YouTube data analysis, engagement metrics, and recommendation networks
        </p>
      </div>

      <Tabs defaultValue="channel" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="channel" className="gap-2">
            <Users className="h-4 w-4" />
            Channel Analysis
          </TabsTrigger>
          <TabsTrigger value="video" className="gap-2">
            <Video className="h-4 w-4" />
            Video Analysis
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="gap-2">
            <Network className="h-4 w-4" />
            Recommendation Network
          </TabsTrigger>
        </TabsList>

        <TabsContent value="channel">
          <ChannelAnalysisPanel />
        </TabsContent>

        <TabsContent value="video">
          <VideoAnalysisPanel />
        </TabsContent>

        <TabsContent value="recommendations">
          <RecommendationAnalysisPanel />
        </TabsContent>
      </Tabs>
    </div>
  )
}