#!/usr/bin/env python3
"""
Temporary analysis script to understand the rowing sensor data
This will help us map the channels and understand the data format
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal, stats
import pandas as pd

def parse_anc_file(filepath):
    """Parse the .ANC file format"""
    print("📂 Parsing .ANC file...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Parse header information
    header_info = {}
    data_start = 0
    
    for i, line in enumerate(lines):
        if 'Duration' in line:
            duration = line.split('Duration(Sec.):')[1].split('#')[0].strip()
            header_info['duration'] = float(duration)
        if 'PreciseRate' in line:
            rate = line.split('PreciseRate:')[1].strip()
            header_info['sample_rate'] = float(rate)
        if '#Channels' in line:
            n_channels = line.split('#Channels:')[1].split()[0].strip()
            header_info['n_channels'] = int(n_channels)
        if line.startswith('Name'):
            # Channel names
            channels = line.strip().split('\t')[1:]  # Skip 'Name'
            channels = [ch.strip() for ch in channels if ch.strip()]
            header_info['channels'] = channels
            header_info['n_channels'] = len(channels)
            data_start = i + 3  # Skip Name, Rate, Range lines
            break
    
    print(f"  Duration: {header_info['duration']:.2f} seconds")
    print(f"  Sample Rate: {header_info['sample_rate']:.0f} Hz")
    print(f"  Channels: {header_info['channels']}")
    
    # Parse data
    data = []
    timestamps = []
    
    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= header_info['n_channels'] + 1:
            try:
                timestamps.append(float(parts[0]))
                values = [int(parts[i]) for i in range(1, header_info['n_channels'] + 1)]
                data.append(values)
            except ValueError:
                continue
    
    data = np.array(data)
    timestamps = np.array(timestamps)
    
    print(f"  Loaded {len(data)} samples")
    print(f"  Data shape: {data.shape}")
    
    return timestamps, data, header_info

def analyze_rowing_strokes(timestamps, data, channels):
    """Identify and analyze rowing stroke cycles"""
    print("\n🚣 Analyzing rowing stroke patterns...")
    
    # The back potentiometer (seat position) should show clear cyclical movement
    back_pot_idx = channels.index('Back Pot')
    seat_position = data[:, back_pot_idx]
    
    # Find peaks (forward position) and troughs (back position) in seat movement
    # First smooth the data
    from scipy.ndimage import gaussian_filter1d
    seat_smooth = gaussian_filter1d(seat_position, sigma=20)
    
    # Find peaks (assuming higher values = more forward)
    peaks, _ = signal.find_peaks(seat_smooth, distance=500, prominence=100)
    troughs, _ = signal.find_peaks(-seat_smooth, distance=500, prominence=100)
    
    print(f"  Detected {len(peaks)} potential stroke peaks")
    print(f"  Detected {len(troughs)} potential stroke troughs")
    
    if len(peaks) > 1:
        stroke_durations = np.diff(peaks) / 2000.0  # Convert to seconds
        print(f"  Avg stroke duration: {np.mean(stroke_durations):.2f}s")
        print(f"  Stroke rate: {60/np.mean(stroke_durations):.1f} strokes/min")
    
    return peaks, troughs, seat_smooth

def plot_full_overview(timestamps, data, channels):
    """Plot all channels over time to see overall patterns"""
    print("\n📊 Creating full data overview...")
    
    n_channels = len(channels)
    fig, axes = plt.subplots(n_channels, 1, figsize=(15, 2.5*n_channels))
    fig.suptitle('Full Recording - All Sensor Channels', fontsize=14, fontweight='bold')
    
    colors = plt.cm.tab10(np.linspace(0, 1, n_channels))
    
    for i, (ax, channel, color) in enumerate(zip(axes, channels, colors)):
        ax.plot(timestamps, data[:, i], linewidth=0.5, color=color, alpha=0.8)
        ax.set_ylabel(f'{channel}\n(raw ADC)', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(timestamps[0], timestamps[-1])
        
        # Add stats
        mean_val = np.mean(data[:, i])
        std_val = np.std(data[:, i])
        min_val = np.min(data[:, i])
        max_val = np.max(data[:, i])
        ax.text(0.02, 0.95, f'μ={mean_val:.0f}, σ={std_val:.0f}\nmin={min_val:.0f}, max={max_val:.0f}',
                transform=ax.transAxes, fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    axes[-1].set_xlabel('Time (seconds)', fontsize=11)
    plt.tight_layout()
    plt.savefig('rowing_data_overview.png', dpi=150, bbox_inches='tight')
    print("  Saved: rowing_data_overview.png")
    
    return fig

def plot_single_stroke(timestamps, data, channels, peaks):
    """Plot a detailed view of a single rowing stroke"""
    print("\n🔍 Creating detailed single-stroke view...")
    
    if len(peaks) < 2:
        print("  Not enough strokes detected for single stroke analysis")
        return None
    
    # Use the middle stroke for analysis
    stroke_idx = len(peaks) // 2
    start_sample = peaks[stroke_idx]
    end_sample = peaks[stroke_idx + 1] if stroke_idx + 1 < len(peaks) else start_sample + 2000
    
    stroke_time = timestamps[start_sample:end_sample]
    stroke_data = data[start_sample:end_sample, :]
    
    # Normalize time to start at 0
    stroke_time = stroke_time - stroke_time[0]
    
    n_channels = len(channels)
    fig, axes = plt.subplots(n_channels, 1, figsize=(12, 2.5*n_channels))
    fig.suptitle(f'Single Rowing Stroke Detail (Stroke #{stroke_idx+1})', fontsize=14, fontweight='bold')
    
    colors = plt.cm.tab10(np.linspace(0, 1, n_channels))
    
    for i, (ax, channel, color) in enumerate(zip(axes, channels, colors)):
        ax.plot(stroke_time, stroke_data[:, i], linewidth=1.5, color=color, marker='o', 
                markersize=2, markevery=50)
        ax.set_ylabel(f'{channel}\n(raw ADC)', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Highlight phases
        # Assume first half is recovery, second half is drive (simplified)
        mid_point = len(stroke_time) // 2
        ax.axvspan(stroke_time[0], stroke_time[mid_point], alpha=0.1, color='blue', label='Recovery?')
        ax.axvspan(stroke_time[mid_point], stroke_time[-1], alpha=0.1, color='red', label='Drive?')
        
        if i == 0:
            ax.legend(loc='upper right', fontsize=8)
    
    axes[-1].set_xlabel('Time in Stroke (seconds)', fontsize=11)
    plt.tight_layout()
    plt.savefig('rowing_single_stroke.png', dpi=150, bbox_inches='tight')
    print("  Saved: rowing_single_stroke.png")
    
    return fig

def analyze_correlations(data, channels):
    """Analyze correlations between channels to understand relationships"""
    print("\n🔗 Analyzing channel correlations...")
    
    # Calculate correlation matrix
    corr_matrix = np.corrcoef(data.T)
    
    # Create correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    
    # Set ticks and labels
    ax.set_xticks(np.arange(len(channels)))
    ax.set_yticks(np.arange(len(channels)))
    ax.set_xticklabels(channels, rotation=45, ha='right')
    ax.set_yticklabels(channels)
    
    # Add correlation values as text
    for i in range(len(channels)):
        for j in range(len(channels)):
            text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)
    
    ax.set_title('Sensor Channel Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
    plt.colorbar(im, ax=ax, label='Correlation Coefficient')
    plt.tight_layout()
    plt.savefig('rowing_correlations.png', dpi=150, bbox_inches='tight')
    print("  Saved: rowing_correlations.png")
    
    # Print interesting correlations
    print("\n  High positive correlations (> 0.7):")
    for i in range(len(channels)):
        for j in range(i+1, len(channels)):
            if corr_matrix[i, j] > 0.7:
                print(f"    {channels[i]} ↔ {channels[j]}: {corr_matrix[i, j]:.3f}")
    
    print("\n  High negative correlations (< -0.7):")
    for i in range(len(channels)):
        for j in range(i+1, len(channels)):
            if corr_matrix[i, j] < -0.7:
                print(f"    {channels[i]} ↔ {channels[j]}: {corr_matrix[i, j]:.3f}")
    
    return corr_matrix

def analyze_load_cell_pairs(data, channels):
    """Analyze the load cell pairs to understand their meaning"""
    print("\n⚖️  Analyzing Load Cell Characteristics...")
    
    lc_indices = [i for i, ch in enumerate(channels) if ch.startswith('LC')]
    
    print(f"\n  Load Cell Statistics:")
    for idx in lc_indices:
        channel_data = data[:, idx]
        print(f"    {channels[idx]}:")
        print(f"      Mean: {np.mean(channel_data):.1f}")
        print(f"      Std:  {np.std(channel_data):.1f}")
        print(f"      Min:  {np.min(channel_data):.1f}")
        print(f"      Max:  {np.max(channel_data):.1f}")
        print(f"      Range: {np.max(channel_data) - np.min(channel_data):.1f}")
    
    # Check if pairs are similar (suggesting they measure similar things)
    if len(lc_indices) >= 4:
        lc1_data = data[:, lc_indices[0]]
        lc2_data = data[:, lc_indices[1]]
        lc3_data = data[:, lc_indices[2]]
        lc4_data = data[:, lc_indices[3]]
        
        # Calculate magnitude for each foot (if they're vector components)
        left_magnitude = np.sqrt(lc1_data**2 + lc2_data**2)
        right_magnitude = np.sqrt(lc3_data**2 + lc4_data**2)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot LC pairs
        time_subset = np.arange(0, len(lc1_data), 1)
        
        axes[0, 0].plot(time_subset, lc1_data[time_subset], label='LC1', alpha=0.7)
        axes[0, 0].plot(time_subset, lc2_data[time_subset], label='LC2', alpha=0.7)
        axes[0, 0].set_title('Left Foot Load Cells (LC1 & LC2)', fontweight='bold')
        axes[0, 0].set_xlabel('Sample')
        axes[0, 0].set_ylabel('Raw ADC Value')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[0, 1].plot(time_subset, lc3_data[time_subset], label='LC3', alpha=0.7)
        axes[0, 1].plot(time_subset, lc4_data[time_subset], label='LC4', alpha=0.7)
        axes[0, 1].set_title('Right Foot Load Cells (LC3 & LC4)', fontweight='bold')
        axes[0, 1].set_xlabel('Sample')
        axes[0, 1].set_ylabel('Raw ADC Value')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot magnitudes
        axes[1, 0].plot(time_subset, left_magnitude[time_subset], label='Left Foot Magnitude', 
                       color='blue', linewidth=1.5)
        axes[1, 0].plot(time_subset, right_magnitude[time_subset], label='Right Foot Magnitude', 
                       color='red', linewidth=1.5)
        axes[1, 0].set_title('Combined Force Magnitude per Foot', fontweight='bold')
        axes[1, 0].set_xlabel('Sample')
        axes[1, 0].set_ylabel('Magnitude (√(LC1²+LC2²))')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Scatter plot: LC1 vs LC2
        axes[1, 1].scatter(lc1_data[::10], lc2_data[::10], alpha=0.3, s=1, label='Left Foot')
        axes[1, 1].scatter(lc3_data[::10], lc4_data[::10], alpha=0.3, s=1, label='Right Foot')
        axes[1, 1].set_title('Load Cell Component Relationships', fontweight='bold')
        axes[1, 1].set_xlabel('First LC Component')
        axes[1, 1].set_ylabel('Second LC Component')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axhline(y=0, color='k', linestyle='--', linewidth=0.5)
        axes[1, 1].axvline(x=0, color='k', linestyle='--', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig('load_cell_analysis.png', dpi=150, bbox_inches='tight')
        print("  Saved: load_cell_analysis.png")

def main():
    filepath = '/Users/aashirmeeran/Library/Mobile Documents/com~apple~CloudDocs/University/Year-4/Capstone/BME470-Capstone-FES-rowing/rowing01.ANC'
    
    print("=" * 60)
    print("🔬 ROWING DATA ANALYSIS")
    print("=" * 60)
    
    # Parse the file
    timestamps, data, header_info = parse_anc_file(filepath)
    channels = header_info['channels']
    
    # Analysis 1: Full overview plots
    plot_full_overview(timestamps, data, channels)
    
    # Detect rowing strokes
    peaks, troughs, seat_smooth = analyze_rowing_strokes(timestamps, data, channels)
    
    # Analysis 2: Single stroke detail
    plot_single_stroke(timestamps, data, channels, peaks)
    
    # Analysis 3: Correlations
    corr_matrix = analyze_correlations(data, channels)
    
    # Bonus: Load cell specific analysis
    analyze_load_cell_pairs(data, channels)
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - rowing_data_overview.png")
    print("  - rowing_single_stroke.png")
    print("  - rowing_correlations.png")
    print("  - load_cell_analysis.png")
    print("\nKey observations will help us understand:")
    print("  1. Which LC channels represent which force components")
    print("  2. How sensor values change during rowing strokes")
    print("  3. Relationships between different sensors")
    
if __name__ == "__main__":
    main()

