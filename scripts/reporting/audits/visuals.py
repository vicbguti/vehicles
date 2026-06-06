import os
import sys
import json
import yaml
from glob import glob
import matplotlib.pyplot as plt

def main():
    config_path = os.path.join(os.path.dirname(__file__), '../../../config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    paths = config['paths']
    cache_dir = os.path.join(paths['reports_dir'], 'cache')
    figures_dir = os.path.join(paths['reports_dir'], 'figures', 'audits')
    os.makedirs(figures_dir, exist_ok=True)
    
    # Load annual row counts
    annual_dirs = sorted(glob(os.path.join(cache_dir, 'annual/*')))
    years = []
    counts = []
    
    for dir_path in annual_dirs:
        if not os.path.isdir(dir_path):
            continue
        year = os.path.basename(dir_path)
        with open(os.path.join(dir_path, 'record_count.json'), 'r') as f:
            data = json.load(f)
            years.append(int(year))
            counts.append(data['row_count'])
            
    # Sort by year
    sorted_data = sorted(zip(years, counts))
    years_sorted, counts_sorted = zip(*sorted_data)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot bars for row counts
    bars = plt.bar(years_sorted, [c / 1000 for c in counts_sorted], color='#2b5c8f', width=0.6, label='Registrations')
    
    # Annotate bar heights
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 10, f'{int(yval)}k', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333')
        
    # Styling
    plt.title('Annual Vehicle Registration Volume (Ecuador, 2017-2026)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Year', fontsize=11, labelpad=10)
    plt.ylabel('Registrations (Thousands)', fontsize=11, labelpad=10)
    plt.xticks(years_sorted)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Remove top and right spines
    for spine in ['top', 'right']:
        plt.gca().spines[spine].set_visible(False)
        
    plt.tight_layout()
    
    # Save the figure
    out_path = os.path.join(figures_dir, 'volume_trends.png')
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Volume trends chart saved to {out_path}")

if __name__ == '__main__':
    main()
