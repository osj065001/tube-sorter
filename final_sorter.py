import pandas as pd
import os
import re

def main():
    metadata_file = "channel_videos_metadata.csv"
    mapping_file = "playlist_video_mapping.csv"
    output_dir = "categorized_by_playlist"
    exclude_playlist = "특별영상"

    # Check dependencies
    if not os.path.exists(metadata_file) or not os.path.exists(mapping_file):
        print("Error: Required CSV files (metadata or mapping) not found.")
        return

    # Load data
    print("Loading data...")
    df_meta = pd.read_csv(metadata_file)
    df_map = pd.read_csv(mapping_file)

    # 1. Filter out '특별영상' and potentially others if needed
    print(f"Filtering out playlist: {exclude_playlist}")
    df_map_filtered = df_map[df_map['playlist_title'] != exclude_playlist]

    # 2. Merge mapping with metadata to get full info for playlist items
    # Note: A video can belong to multiple playlists. 
    # inner join ensures we only keep videos that are in the filtered playlists.
    final_df = pd.merge(df_map_filtered, df_meta, on='video_id', how='inner')

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # 3. Save by playlist
    playlists = final_df['playlist_title'].unique()
    print(f"\nProcessing {len(playlists)} valid playlists: {playlists}")
    print("-" * 40)

    for playlist in playlists:
        playlist_data = final_df[final_df['playlist_title'] == playlist]
        
        # Select and reorder columns for the output
        # (Using metadata columns + position in playlist)
        output_cols = ['video_id', 'title', 'url', 'published_at', 'view_count', 'duration', 'position']
        # Use existing columns from merge
        cols_to_save = [col for col in output_cols if col in playlist_data.columns]
        
        # Sanitize filename
        safe_name = re.sub(r'[\\/*?:"<>|]', "", playlist)
        output_path = os.path.join(output_dir, f"{safe_name}.csv")
        
        playlist_data[cols_to_save].to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {safe_name}.csv ({len(playlist_data)} videos)")

    print("-" * 40)
    print(f"Total videos classified into playlists: {len(final_df)}")
    print(f"Videos skipped: {len(df_meta) - final_df['video_id'].nunique()} (Not in selected playlists)")

if __name__ == "__main__":
    main()
