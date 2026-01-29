import pandas as pd
from googleapiclient.discovery import build

# --- CONFIGURATION ---
API_KEY = "AIzaSyDytuGmgrFwBxMYt3cM4j0V9H5o_b2idu0"
YOUTUBE = build("youtube", "v3", developerKey=API_KEY)


# Replace with the Channel ID you want to scrape (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw')
CHANNEL_ID = "UCpg-rSVxo3EgwEmWHl2nN9A" 

def get_uploads_playlist_id(channel_id):
    """
    Fetches the ID of the 'Uploads' playlist for a given channel.
    This playlist contains all the public videos of the channel.
    """
    request = YOUTUBE.channels().list(
        id=channel_id,
        part="contentDetails"
    )
    response = request.execute()
    
    if not response.get("items"):
        raise ValueError(f"Channel ID {channel_id} not found.")
        
    # Extract the uploads playlist ID
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_all_videos_from_playlist(playlist_id):
    """
    Iterates through a playlist and returns a list of all videos in it.
    """
    videos = []
    next_page_token = None
    
    print(f"Fetching videos from playlist: {playlist_id}...")

    while True:
        request = YOUTUBE.playlistItems().list(
            playlistId=playlist_id,
            part="snippet",
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            
            # Skip private/deleted videos usually indicated by missing resourceId
            if "resourceId" not in snippet:
                continue

            video_data = {
                "Video Title": snippet["title"],
                "Channel": snippet["channelTitle"],
                "Published Date": snippet["publishedAt"],
                "Video URL": f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}",
                "Description": snippet["description"],
                "Video ID": snippet["resourceId"]["videoId"]
            }
            videos.append(video_data)

        # Check if there are more pages
        next_page_token = response.get("nextPageToken")
        
        print(f"Collected {len(videos)} videos so far...")
        
        if not next_page_token:
            break
            
    return videos

def main():
    try:
        # Step 1: Get the Uploads Playlist ID
        print(f"Locating uploads playlist for Channel ID: {CHANNEL_ID}...")
        uploads_playlist_id = get_uploads_playlist_id(CHANNEL_ID)
        
        # Step 2: Fetch all videos from that playlist
        all_data = fetch_all_videos_from_playlist(uploads_playlist_id)

        # Step 3: Export to Excel
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Clean up date format
            df['Published Date'] = pd.to_datetime(df['Published Date']).dt.date
            
            filename = f"Channel_Videos_{CHANNEL_ID}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\nDone! {len(all_data)} videos exported to {filename}.")
        else:
            print("No videos found for this channel.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()