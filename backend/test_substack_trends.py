#!/usr/bin/env python3
"""
Test Substack trend analysis
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.analyzers.substack_trend_analyzer import analyze_substack_trends

def main():
    print("=" * 60)
    print("📊 Substack Trend Analysis Test")
    print("=" * 60)
    
    # Test with different time periods
    for days in [7, 14, 30]:
        print(f"\n📅 Analyzing last {days} days...")
        
        try:
            trends = analyze_substack_trends(days)
            
            print(f"✅ Analysis complete!")
            print(f"   Total articles: {trends.get('total_articles', 0)}")
            
            # Show top topics
            if trends.get('topic_trends', {}).get('top_topics'):
                print("\n🔥 Top Topics:")
                for topic in trends['topic_trends']['top_topics'][:5]:
                    print(f"   • {topic['term']}: {topic['articles']} articles")
            
            # Show most active authors
            if trends.get('author_trends', {}).get('most_active'):
                print("\n✍️ Most Active Authors:")
                for author in trends['author_trends']['most_active'][:3]:
                    print(f"   • {author['author']}: {author['articles']} articles")
            
            # Show emerging themes
            if trends.get('emerging_themes'):
                print("\n🚀 Emerging Themes:")
                for theme in trends['emerging_themes'][:3]:
                    print(f"   • {theme['theme']} ({theme['type']}): {theme['growth']}")
            
            # Show velocity trends
            if trends.get('velocity_trends'):
                rising = [t for t in trends['velocity_trends'] if t.get('trend') == 'rising']
                if rising:
                    print(f"\n📈 Rising Topics ({len(rising)}):")
                    for topic in rising[:3]:
                        print(f"   • {topic['topic']}: {topic['velocity']:.1%} growth")
            
            # Save full results to file
            output_file = f"substack_trends_{days}days.json"
            with open(output_file, 'w') as f:
                json.dump(trends, f, indent=2, default=str)
            print(f"\n💾 Full results saved to {output_file}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()