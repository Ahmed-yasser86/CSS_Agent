# YouTube Computational Social Science Research Module

A research-grade tool for YouTube data acquisition, analysis, and computational social science research.

## Overview

This module provides a comprehensive framework for analyzing YouTube channels, videos, and recommendation networks with research-grade features including:

- **Provenance tracking**: Complete history of data collection runs
- **Longitudinal analysis**: Historical observations and temporal patterns
- **Comparative research**: Channel and video comparison tools
- **Network analysis**: Recommendation network analysis with NetworkX
- **Sampling strategies**: Research-grade sampling for comparative analysis
- **Excel persistence**: Research-friendly data storage and export

## Features

### Channel Analysis
- Comprehensive channel metadata extraction
- Video collection and sampling
- Upload pattern analysis
- Engagement metrics and analytics
- Comparative channel analysis

### Video Analysis
- Video metadata and statistics extraction
- Comment collection and analysis
- Temporal engagement patterns
- Sentiment and content analysis
- Comparative video analysis

### Recommendation Network Analysis
- Recommendation network extraction
- Network graph analysis with NetworkX
- Centrality and community detection
- Temporal recommendation patterns
- Channel diversity analysis

## Installation

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Requirements

The module requires the following Python packages:

```
yt-dlp>=2023.11.16
pandas>=1.5.0
openpyxl>=3.0.0
networkx>=2.8.0
pydantic>=1.10.0
fastapi>=0.95.0
uvicorn>=0.22.0
```

## Usage

### Command Line Interface

```bash
# Analyze a channel
python main.py analyze-channel https://www.youtube.com/@ExampleChannel

# Analyze a video
python main.py analyze-video https://www.youtube.com/watch?v=examplevideo

# Analyze video recommendations
python main.py analyze-recommendations https://www.youtube.com/watch?v=examplevideo

# Get channel analytics
python main.py get-channel-analytics channel123

# Compare multiple channels
python main.py compare-channels channel1 channel2 channel3
```

### API Server

```bash
# Start the API server
uvicorn api.endpoints:app --reload
```

API documentation will be available at `http://localhost:8000/docs`

### Python API

```python
from YouTubeComputationalSocialScience.services.channel_service import ChannelService
from YouTubeComputationalSocialScience.services.video_service import VideoService
from YouTubeComputationalSocialScience.services.recommendation_service import RecommendationService
from YouTubeComputationalSocialScience.persistence.excel_repository import (
    ExcelChannelRepository, 
    ExcelVideoRepository, 
    ExcelCommentRepository, 
    ExcelRecommendationRepository
)

# Initialize repositories
channel_repo = ExcelChannelRepository()
video_repo = ExcelVideoRepository()
comment_repo = ExcelCommentRepository()
recommendation_repo = ExcelRecommendationRepository()

# Initialize services
channel_service = ChannelService(channel_repo, video_repo, comment_repo)
video_service = VideoService(video_repo, comment_repo)
recommendation_service = RecommendationService(video_repo, recommendation_repo)

# Analyze a channel
result = channel_service.analyze_channel("https://www.youtube.com/@ExampleChannel")

# Analyze a video
result = video_service.analyze_video("https://www.youtube.com/watch?v=examplevideo")

# Analyze recommendations
result = recommendation_service.analyze_video_recommendations("https://www.youtube.com/watch?v=examplevideo")
```

## Project Structure

```
YouTubeComputationalSocialScience/
├── domain/                  # Domain models and business logic
│   ├── models.py            # Core domain models
│   ├── analytics.py         # Analytics functions
│   └── sampling.py         # Sampling strategies
│
├── acquisition/             # Data acquisition layer
│   ├── youtube_scraper.py   # YouTube data scraper
│   └── data_extractor.py    # Data extraction and normalization
│
├── persistence/             # Data persistence layer
│   ├── repository.py        # Repository interfaces
│   └── excel_repository.py # Excel implementation
│
├── services/                # Service layer
│   ├── channel_service.py   # Channel analysis service
│   ├── video_service.py     # Video analysis service
│   └── recommendation_service.py # Recommendation analysis service
│
├── api/                     # API layer
│   └── endpoints.py         # FastAPI endpoints
│
├── tests/                   # Test files
│   ├── test_channel_service.py
│   ├── test_video_service.py
│   └── test_recommendation_service.py
│
├── main.py                  # CLI entry point
└── README.md                # Project documentation
```

## Research Features

### Provenance Tracking

Every data collection run is tracked with:
- Unique collection run ID
- Collection timestamp
- Collection type (channel, video, recommendation)
- Target URL/ID
- Collection status and errors
- Counts of successfully collected items

### Historical Observations

The system maintains historical observations for:
- Channel statistics (subscribers, views, videos)
- Video statistics (views, likes, comments)
- Recommendation networks

This enables longitudinal analysis of how channels, videos, and recommendation patterns evolve over time.

### Sampling Strategies

Research-grade sampling strategies include:
- **Stratified sampling**: By time periods for longitudinal analysis
- **Top performers**: Focus on most popular content
- **Temporal sampling**: Analyze content from specific time periods
- **Random sampling**: Representative samples for comparative analysis

### Network Analysis

Recommendation networks are analyzed using NetworkX with:
- Centrality measures (in-degree, out-degree, betweenness)
- Network density and connectivity
- Channel diversity metrics
- Reciprocity analysis
- Temporal network evolution

## Data Storage

Data is stored in Excel files for research accessibility:

- **Channels**: `channels.xlsx`
- **Videos**: `videos.xlsx`
- **Comments**: `comments.xlsx`
- **Recommendations**: `recommendations.xlsx`
- **Collection Runs**: `collection_runs.xlsx`

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or feedback, please contact the research team at [research@example.com].

## Acknowledgments

- yt-dlp for YouTube data extraction
- NetworkX for graph analysis
- pandas and openpyxl for data persistence
- FastAPI for the web API