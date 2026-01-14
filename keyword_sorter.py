import pandas as pd
import os

def main():
    input_file = "channel_videos_metadata.csv"
    output_dir = "keyword_categorized"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    df = pd.read_csv(input_file)
    print(f"Total videos to analyze: {len(df)}")

    # Define keyword mapping
    # (Category Name, Keywords List)
    mapping = {
        "새벽예배": ["새벽"],
        "수요예배": ["수요"],
        "금요철야": ["금요", "철야"],
        "주일예배": ["주일"],
        "청년부예배": ["청년"]
    }

    # Tracking stats
    stats = {}
    total_classified = 0

    for category, keywords in mapping.items():
        # 1. Basic keyword match
        # 2. Exclude "특별" as requested
        mask = (df['title'].str.contains('|'.join(keywords), case=False, na=False) & 
                ~df['title'].str.contains("특별", case=False, na=False))
        
        category_df = df[mask]
        
        if not category_df.empty:
            output_path = os.path.join(output_dir, f"{category}.csv")
            category_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            stats[category] = len(category_df)
            total_classified += len(category_df)
            print(f"Saved: {category}.csv ({len(category_df)} videos)")
        else:
            stats[category] = 0

    print("-" * 40)
    print(f"Total classified: {total_classified}")
    print(f"Total skipped: {len(df) - total_classified} (Including '특별' or no matches)")

if __name__ == "__main__":
    main()
