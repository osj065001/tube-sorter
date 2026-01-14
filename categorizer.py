import pandas as pd
import os
import re

def extract_category(title):
    """
    Extracts the category (playlist name) from the video title.
    Expected pattern: "예수산소망교회 [Category](Date)"
    """
    # Pattern 1: Standard format "예수산소망교회 [Category]("
    # Matches "예수산소망교회 새벽예배(2024..." -> "새벽예배"
    match = re.search(r"예수산소망교회\s+(.+?)\s*\(", str(title))
    if match:
        category = match.group(1).strip()
        # Normalize spaces (e.g., "주일 2부 예배" -> "주일2부예배")
        return category.replace(" ", "")
    
    # Pattern 2: Keyword based fallback for titles not following the standard format
    title_norm = title.replace(" ", "")
    if "새벽" in title_norm:
        return "새벽예배"
    elif "수요" in title_norm:
        return "수요예배"
    elif "금요" in title_norm or "철야" in title_norm:
        return "금요철야"
    elif "주일" in title_norm:
        if "1부" in title_norm: return "주일1부예배"
        if "2부" in title_norm or "2시" in title_norm: return "주일2부예배"
        if "3부" in title_norm: return "주일3부예배"
        return "주일예배_기타"
    elif "청년" in title_norm:
        return "청년부예배"
    elif "특송" in title_norm or "찬양" in title_norm or "워십" in title_norm:
        return "찬양_특송"
    
    return "기타"

def main():
    input_file = "channel_videos_metadata.csv"
    output_dir = "categorized_videos"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Apply categorization
    df['category'] = df['title'].apply(extract_category)
    
    # Get unique categories
    categories = df['category'].unique()
    
    print(f"Found {len(categories)} categories: {categories}")
    print("-" * 30)

    # Save extracted files
    for category in categories:
        category_df = df[df['category'] == category]
        
        # Sanitize filename (remove special chars if any, though our logic produces clean names)
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", category)
        output_path = os.path.join(output_dir, f"{safe_filename}.csv")
        
        category_df.drop(columns=['category']).to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {safe_filename}.csv ({len(category_df)} videos)")

if __name__ == "__main__":
    main()
