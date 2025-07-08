# advanced sql queries
import sqlite3
from datetime import datetime

class AdvancedQueries:
    def __init__(self, db_path="patch.db"):
        self.db_path = db_path

    def get_hero_balance_trends(self):
        """complex query showing hero balance changes over time"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
            WITH hero_stats AS (
                SELECT 
                    h.name,
                    p.version,
                    p.id as patch_id,
                    COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buffs,
                    COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerfs,
                    COUNT(*) as total_changes,
                    ROW_NUMBER() OVER (ORDER BY p.id) as patch_order
                FROM heroes h
                LEFT JOIN patch_changes pc ON h.id = pc.hero_id
                LEFT JOIN patches p ON pc.patch_id = p.id
                WHERE p.id IS NOT NULL
                GROUP BY h.name, p.version, p.id
            ),
            hero_trends AS (
                SELECT 
                    name,
                    patch_order,
                    buffs,
                    nerfs,
                    total_changes,
                    SUM(buffs) OVER (PARTITION BY name ORDER BY patch_order) as cumulative_buffs,
                    SUM(nerfs) OVER (PARTITION BY name ORDER BY patch_order) as cumulative_nerfs,
                    AVG(total_changes) OVER (PARTITION BY name ORDER BY patch_order ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as rolling_avg_changes
                FROM hero_stats
            )
            SELECT 
                name,
                cumulative_buffs - cumulative_nerfs as balance_score,
                ROUND(rolling_avg_changes, 2) as avg_changes_per_patch,
                CASE 
                    WHEN cumulative_buffs > cumulative_nerfs THEN 'buffed_overall'
                    WHEN cumulative_nerfs > cumulative_buffs THEN 'nerfed_overall'
                    ELSE 'balanced'
                END as trend
            FROM hero_trends
            WHERE patch_order = (SELECT MAX(patch_order) FROM hero_trends ht2 WHERE ht2.name = hero_trends.name)
            ORDER BY balance_score DESC
            LIMIT 10
            """
            
            cursor.execute(query)
            return cursor.fetchall()

    def get_item_popularity_analysis(self):
        """window functions for item usage trends"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
            WITH item_stats AS (
                SELECT 
                    i.name,
                    i.category,
                    COUNT(*) as mention_count,
                    COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buff_count,
                    COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerf_count,
                    RANK() OVER (PARTITION BY i.category ORDER BY COUNT(*) DESC) as category_rank,
                    PERCENT_RANK() OVER (ORDER BY COUNT(*)) as popularity_percentile
                FROM items i
                LEFT JOIN patch_changes pc ON i.id = pc.item_id
                GROUP BY i.id, i.name, i.category
                HAVING COUNT(*) > 0
            )
            SELECT 
                category,
                name,
                mention_count,
                buff_count,
                nerf_count,
                category_rank,
                ROUND(popularity_percentile * 100, 1) as popularity_score,
                CASE 
                    WHEN buff_count > nerf_count THEN 'needs_nerf'
                    WHEN nerf_count > buff_count THEN 'needs_buff'
                    ELSE 'balanced'
                END as balance_suggestion
            FROM item_stats
            WHERE category_rank <= 5
            ORDER BY category, category_rank
            """
            
            cursor.execute(query)
            return cursor.fetchall()

    def get_patch_impact_metrics(self):
        """aggregation queries for patch analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                p.version,
                p.id,
                COUNT(pc.id) as total_changes,
                COUNT(DISTINCT pc.hero_id) as heroes_affected,
                COUNT(DISTINCT pc.item_id) as items_affected,
                COUNT(pm.id) as media_files,
                ROUND(
                    COUNT(pc.id) * 1.0 / 
                    NULLIF((COUNT(DISTINCT pc.hero_id) + COUNT(DISTINCT pc.item_id)), 0), 
                    2
                ) as changes_per_entity,
                COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buffs,
                COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerfs,
                COUNT(CASE WHEN pc.change_type = 'other' THEN 1 END) as other_changes,
                CASE 
                    WHEN COUNT(pc.id) > 200 THEN 'major'
                    WHEN COUNT(pc.id) > 50 THEN 'medium'
                    ELSE 'minor'
                END as patch_size
            FROM patches p
            LEFT JOIN patch_changes pc ON p.id = pc.patch_id
            LEFT JOIN patch_media pm ON p.id = pm.patch_id
            WHERE p.processed = TRUE
            GROUP BY p.id, p.version
            HAVING COUNT(pc.id) > 0
            ORDER BY total_changes DESC
            LIMIT 15
            """
            
            cursor.execute(query)
            return cursor.fetchall()

    def get_database_insights(self):
        """comprehensive database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # total counts
            cursor.execute("SELECT COUNT(*) FROM patches WHERE processed = TRUE")
            processed_patches = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patch_changes")
            total_changes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patch_media")
            total_media = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM heroes")
            total_heroes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM items")
            total_items = cursor.fetchone()[0]
            
            # change type distribution
            cursor.execute("""
                SELECT change_type, COUNT(*) as count, 
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM patch_changes), 1) as percentage
                FROM patch_changes 
                GROUP BY change_type 
                ORDER BY count DESC
            """)
            change_distribution = cursor.fetchall()
            
            return {
                'processed_patches': processed_patches,
                'total_changes': total_changes,
                'total_media': total_media,
                'total_heroes': total_heroes,
                'total_items': total_items,
                'change_distribution': change_distribution
            }

def run_analytics():
    """demonstrate advanced sql capabilities"""
    analytics = AdvancedQueries()
    
    print("=== ADVANCED SQL ANALYTICS ===\n")
    
    # database overview
    insights = analytics.get_database_insights()
    print(f"database overview:")
    print(f"   processed patches: {insights['processed_patches']}")
    print(f"   total changes: {insights['total_changes']:,}")
    print(f"   media files: {insights['total_media']}")
    print(f"   heroes tracked: {insights['total_heroes']}")
    print(f"   items tracked: {insights['total_items']}")
    print()
    
    print("change type distribution:")
    for change_type, count, percentage in insights['change_distribution']:
        print(f"   {change_type}: {count:,} ({percentage}%)")
    print()
    
    # hero balance analysis
    print("hero balance trends (top 10):")
    hero_trends = analytics.get_hero_balance_trends()
    for name, balance_score, avg_changes, trend in hero_trends:
        print(f"   {name}: {balance_score:+d} balance, {avg_changes} avg changes ({trend})")
    print()
    
    # item popularity
    print("most changed items by category:")
    item_analysis = analytics.get_item_popularity_analysis()
    current_category = None
    for category, name, mentions, buffs, nerfs, rank, popularity, suggestion in item_analysis:
        if category != current_category:
            print(f"\n   {category}:")
            current_category = category
        print(f"     #{rank} {name}: {mentions} changes ({buffs}b/{nerfs}n) - {suggestion}")
    print()
    
    # patch impact
    print("biggest patches by impact:")
    patch_metrics = analytics.get_patch_impact_metrics()
    for version, patch_id, changes, heroes, items, media, ratio, buffs, nerfs, other, size in patch_metrics[:10]:
        print(f"   {version}: {changes} changes, {heroes}h/{items}i affected ({size})")

if __name__ == "__main__":
    run_analytics()
