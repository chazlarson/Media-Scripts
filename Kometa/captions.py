from pytube import Channel
import os

def download_subtitles_from_channel(channel_url, output_path='.'):
    """
    Downloads subtitles for all videos from a YouTube channel.

    Args:
        channel_url (str): The URL of the YouTube channel.
        output_path (str): The directory to save the subtitles.
    """
    try:
        c = Channel(channel_url)
        print(f"Processing channel: {c.channel_name}")

        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Created output directory: {output_path}")

        video_count = 0
        caption_count = 0

        for video in c.videos:
            video_count += 1
            print(f"\nProcessing video {video_count}: {video.title}")

            try:
                # Check if captions are available
                if video.captions:
                    # You can specify the language code, e.g., 'en' for English
                    # Use video.captions to see all available caption languages
                    if 'en' in video.captions:
                        caption = video.captions['en']
                        print("Downloading English captions...")

                        # Generate a safe filename
                        filename = f"{video.title}.en.srt"
                        safe_filename = "".join(x for x in filename if x.isalnum() or x in "._- ").strip()
                        file_path = os.path.join(output_path, safe_filename)

                        # Save the captions as an .srt file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(caption.generate_srt_file())
                            caption_count += 1
                            print(f"✅ Downloaded and saved captions to: {file_path}")
                    else:
                        print("⚠️ English captions not found for this video. Skipping.")
                else:
                    print("⚠️ No captions available for this video. Skipping.")

            except Exception as e:
                print(f"An error occurred while processing video {video.title}: {e}")

        print(f"\n--- Script finished ---")
        print(f"Successfully processed {len(c.videos)} videos.")
        print(f"Successfully downloaded captions for {caption_count} videos.")

    except Exception as e:
        print(f"An error occurred with the channel URL: {e}")

# --- USAGE ---
# Replace with the URL of the YouTube channel you want to download from
CHANNEL_URL = 'https://www.youtube.com/@freecodecamp'
OUTPUT_FOLDER = './youtube_captions'

download_subtitles_from_channel(CHANNEL_URL, OUTPUT_FOLDER)