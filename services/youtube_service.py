import pandas as pd
from googleapiclient.discovery import build
import os
from datetime import datetime
import isodate  # You might need to add this to requirements.txt

# Store API Key temporarily or pass it in. 
# For this service, we'll accept it as an argument.

def get_uploads_playlist_id(youtube, channel_id):
    """
    Fetches the ID of the 'Uploads' playlist for a given channel.
    """
    request = youtube.channels().list(
        id=channel_id,
        part="contentDetails,snippet"  # Added snippet to get channel name
    )
    response = request.execute()
    
    if not response.get("items"):
        raise ValueError(f"Channel ID {channel_id} not found.")
        
    item = response["items"][0]
    uploads_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_name = item["snippet"]["title"]
    
    return uploads_id, channel_name

def get_video_details(youtube, video_ids):
    """
    Fetches detailed information (duration, tags) for a list of video IDs.
    """
    video_details = {}
    
    # API limits to 50 ids per request
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        request = youtube.videos().list(
            id=",".join(chunk),
            part="contentDetails,snippet"
        )
        response = request.execute()
        
        for item in response.get("items", []):
            vid = item["id"]
            duration_iso = item["contentDetails"].get("duration", "PT0S")
            duration = isodate.parse_duration(duration_iso)
            
            video_details[vid] = {
                "Duration": str(duration),
                "Tags": ",".join(item["snippet"].get("tags", [])),
                "CategoryId": item["snippet"].get("categoryId", "")
            }
            
    return video_details

def fetch_channel_videos_generator(api_key, channel_ids_str):
    """
    Generator that yields progress messages and finally the filename.
    Accepts comma-separated channel IDs.
    """
    try:
        yield f"Connecting to YouTube API..."
        youtube = build("youtube", "v3", developerKey=api_key)
        
        # Split and clean IDs
        channel_ids = [cid.strip() for cid in channel_ids_str.split(',') if cid.strip()]
        
        if not channel_ids:
            yield "Error: No valid Channel IDs provided."
            return

        all_videos = []
        first_channel_name = "Unknown"

        for idx, channel_id in enumerate(channel_ids):
            yield f"--- Processing Channel {idx+1}/{len(channel_ids)}: {channel_id} ---"
            
            try:
                yield f"Resolving Channel ID {channel_id}..."
                uploads_playlist_id, channel_name = get_uploads_playlist_id(youtube, channel_id)
                yield f"Found Channel: {channel_name}"
                
                if idx == 0:
                    first_channel_name = channel_name
                
                videos = []
                next_page_token = None
                page_count = 0
                
                yield f"Starting video fetch for playlist: {uploads_playlist_id}"
        
                while True:
                    page_count += 1
                    # yield f"Fetching page {page_count}..." # Reduce noise
                    
                    request = youtube.playlistItems().list(
                        playlistId=uploads_playlist_id,
                        part="snippet,contentDetails",
                        maxResults=50,
                        pageToken=next_page_token
                    )
                    response = request.execute()
        
                    video_ids_in_batch = []
                    batch_items = []
        
                    for item in response.get("items", []):
                        snippet = item["snippet"]
                        # Skip private/deleted videos
                        if "resourceId" not in snippet:
                            continue
                        vid_id = snippet["resourceId"]["videoId"]
                        video_ids_in_batch.append(vid_id)
                        batch_items.append(item)
        
                    yield f"  > Page {page_count}: Found {len(video_ids_in_batch)} videos."
        
                    # Fetch extra details (duration)
                    if video_ids_in_batch:
                        # yield f"  > Fetching details..."
                        details_map = get_video_details(youtube, video_ids_in_batch)
                        
                        for item in batch_items:
                            snippet = item["snippet"]
                            vid_id = snippet["resourceId"]["videoId"]
                            details = details_map.get(vid_id, {})
                            
                            video_data = {
                                "Video Title": snippet["title"],
                                "Channel": snippet["channelTitle"],
                                "Published Date": pd.to_datetime(snippet["publishedAt"]).date(),
                                "Video URL": f"https://www.youtube.com/watch?v={vid_id}",
                                "Description": snippet["description"],
                                "Video ID": vid_id,
                                "Duration": details.get("Duration", "N/A"),
                                "Tags": details.get("Tags", ""),
                                "Type": "Video"
                            }
                            videos.append(video_data)
        
                    next_page_token = response.get("nextPageToken")
                    
                    if not next_page_token:
                        break
                
                yield f"Channel Complete. Collected {len(videos)} videos."
                all_videos.extend(videos)

            except Exception as e:
                yield f"Error processing channel {channel_id}: {str(e)}"
                continue # Try next channel

        if all_videos:
            yield f"--- Total: {len(all_videos)} videos collected from {len(channel_ids)} channels ---"
            if not os.path.exists('uploads'):
                os.makedirs('uploads')
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_channel_name = "".join([c for c in first_channel_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            
            # If multiple channels, append "and_others"
            if len(channel_ids) > 1:
                filename = f"MultiChannel_{safe_channel_name}_and_others_{timestamp}.xlsx"
            else:
                filename = f"Channel_{safe_channel_name}_{timestamp}.xlsx"

            filepath = os.path.join('uploads', filename)
            abs_path = os.path.abspath(filepath)
            
            df = pd.DataFrame(all_videos)
            df.to_excel(filepath, index=False)
            
            yield f"Success! Saved to: {filename}"
            yield f"Full Path: {abs_path}" 
        else:
             yield "Error: No videos found."

    except Exception as e:
        yield f"Critical Error: {str(e)}"
