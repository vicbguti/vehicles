import os
import sys
import json
import yaml
from glob import glob
import matplotlib.pyplot as plt

def main():
    # Read config for paths
    config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'proposals', 'spatial')
    os.makedirs(figures_dir, exist_ok=True)
    
    # Aggregated classes
    class_counts = {}
    annual_dirs = sorted(glob(os.path.join(cache_dir, 'annual/*')))
    
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
        card_file = os.path.join(dir_path, 'cardinality.json')
        if os.path.exists(card_file):
            with open(card_file, 'r') as f:
                card = json.load(f)
                if 'CLASE' in card and 'top_values' in card['CLASE']:
                    for item in card['CLASE']['top_values']:
                        val = item['value']
                        cnt = item['count']
                        class_counts[val] = class_counts.get(val, 0) + cnt
                        
    if not class_counts:
        print("No class counts found in cache.")
        return
        
    # Sort classes by count descending
    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    classes, counts = zip(*sorted_classes)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Curated modern palette
    colors = ['#1d3557', '#457b9d', '#a8dadc', '#e63946', '#f1faee', '#8d99ae', '#2b2d42', '#ffb703', '#fb8500', '#023047']
    bar_colors = [colors[i % len(colors)] for i in range(len(classes))]
    
    # Plot horizontal bars
    bars = plt.barh(classes[::-1], [c / 1000 for c in counts[::-1]], color=bar_colors[::-1], height=0.6)
    
    # Annotate labels with their exact counts in thousands
    max_val = max(counts) / 1000
    for bar in bars:
        width = bar.get_width()
        plt.text(width + max_val * 0.01, bar.get_y() + bar.get_height()/2.0, 
                 f'{width:.1f}k', ha='left', va='center', fontsize=9, fontweight='bold', color='#333333')
                 
    plt.title('Vehicle Class Distribution (Ecuador, 2017-2026)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Registrations (Thousands)', fontsize=11, labelpad=10)
    plt.ylabel('Vehicle Class', fontsize=11, labelpad=10)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    
    # Remove top and right spines
    for spine in ['top', 'right']:
        plt.gca().spines[spine].set_visible(False)
        
    plt.tight_layout()
    out_path = os.path.join(figures_dir, 'class_distribution.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Class distribution chart saved to {out_path}")

if __name__ == '__main__':
    main()
