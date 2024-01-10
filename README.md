# Spotify Top Artists Data Visualization Project

## Project Overview
This project leverages Spotify's API to extract data on your top artists, loads this data into Amazon S3, and utilizes Tableau for creating dynamic dashboard visualizations. It offers a comprehensive view of your musical preferences and trends over time.

## Architecture
Below is the architecture diagram illustrating the workflow of the project:

![Architecture Diagram](Architecture_Diagram.png "Architecture Diagram")

![Architecture Diagram](Dashboard.png "Architecture Diagram")


## Features
- **Data Extraction**: Utilize Spotify's API to gather data on your top artists, including genres, popularity scores, and related metrics.
- **Data Storage**: Securely load and store extracted data in an Amazon S3 bucket.
- **Data Visualization**: Connect to Tableau for creating interactive dashboards that provide insights into your music listening habits.

## Getting Started

### Prerequisites
- A Spotify account with API access.
- An AWS account with S3 set up.
- Tableau Desktop or Tableau Public for visualization.

## Extracting Data from Spotify API 
1.0 First, we authenticate with Spotify using the `SpotifyOAuth` class, which requires a `client_id`, `client_secret`, `redirect_uri`, and a `scope` for the required permissions.

## Authentication
First, we authenticate with Spotify using the `SpotifyOAuth` class, which requires a `client_id`, `client_secret`, `redirect_uri`, and a `scope` for the required permissions.

### Fetch Top Artists
We use the `current_user_top_artists` method to fetch the user's top artists over a short-term range, limited to 50 artists.

### Extract Artist Information
For each artist, we extract:
- Name
- Genres
- Popularity

### Fetch Top Albums
For each artist, we fetch the top 5 albums, including:
- Name
- ID
- Release date
- Total tracks

### Fetch Top Tracks
For each artist, we fetch their top tracks in the US, and for each track, we gather:
- Name
- Duration (converted from milliseconds to minutes and seconds)
- BPM (Beats Per Minute)
- Mode (Major or Minor)

### Compile Data
All the extracted information is compiled into a list of dictionaries, each containing detailed data about an artist.

The final output is a list of artist information, ready for storage or further analysis.
 


