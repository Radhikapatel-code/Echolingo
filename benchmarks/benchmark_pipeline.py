"""Benchmarking framework for Echolingo pipeline performance.

This module provides tools to measure and analyze the performance of each
stage in the Echolingo dubbing pipeline, including:
- Stage-level timing measurements
- End-to-end latency
- Real-time factor (RTF) calculation
- Resource utilization tracking
- Statistical analysis (mean, median, p95, etc.)
"""

from __future__ import annotations

import json
import os
import sys
import time
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import platform

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""
    video_path: str
    target_lang: str
    output_dir: str
    iterations: int = 3
    warmup_iterations: int = 1
    include_captions: bool = False
    caption_lang: str = "en"


@dataclass
class StageTimings:
    """Timing measurements for each pipeline stage."""
    video_loading: float = 0.0
    audio_extraction: float = 0.0
    transcribe: float = 0.0
    translate: float = 0.0
    tts_generation: float = 0.0
    audio_processing: float = 0.0
    video_composition: float = 0.0
    total_pipeline: float = 0.0


@dataclass
class VideoMetadata:
    """Metadata about the input video."""
    duration: float = 0.0
    resolution: str = ""
    file_size: float = 0.0
    audio_channels: int = 0
    audio_sample_rate: int = 0


@dataclass
class SystemInfo:
    """Information about the benchmark system."""
    cpu: str = ""
    gpu: str = ""
    ram: str = ""
    os: str = ""
    python_version: str = ""
    torch_version: str = ""
    whisper_model: str = ""


@dataclass
class BenchmarkResult:
    """Complete benchmark result for a single run."""
    timestamp: str
    config: BenchmarkConfig
    system_info: SystemInfo
    video_metadata: VideoMetadata
    stage_timings: StageTimings
    success: bool
    error_message: str = ""


class PipelineProfiler:
    """Profiler for measuring pipeline stage performance."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.stage_timings = StageTimings()
        self.start_time = 0.0
        self.stage_start_time = 0.0

    def start_pipeline(self) -> None:
        """Start timing the entire pipeline."""
        self.start_time = time.time()

    def end_pipeline(self) -> None:
        """End timing the entire pipeline."""
        self.stage_timings.total_pipeline = time.time() - self.start_time

    def start_stage(self, stage_name: str) -> None:
        """Start timing a specific stage."""
        self.stage_start_time = time.time()

    def end_stage(self, stage_name: str) -> None:
        """End timing a specific stage and record the duration."""
        duration = time.time() - self.stage_start_time
        setattr(self.stage_timings, stage_name, duration)

    def get_timings(self) -> StageTimings:
        """Get the recorded stage timings."""
        return self.stage_timings


def get_system_info() -> SystemInfo:
    """Collect system information for benchmark metadata."""
    import cpuinfo
    import psutil

    system = SystemInfo()
    system.cpu = cpuinfo.get_cpu_info().get('brand_raw', 'Unknown')
    system.gpu = "Unknown"  # TODO: Implement GPU detection
    system.ram = f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
    system.os = f"{platform.system()} {platform.release()}"
    system.python_version = platform.python_version()

    try:
        import torch
        system.torch_version = torch.__version__
    except ImportError:
        system.torch_version = "Not installed"

    system.whisper_model = "base"  # Default model

    return system


def get_video_metadata(video_path: str) -> VideoMetadata:
    """Extract metadata from the input video."""
    metadata = VideoMetadata()
    
    try:
        from moviepy import VideoFileClip
        video = VideoFileClip(video_path)
        
        metadata.duration = video.duration
        metadata.resolution = f"{video.size[0]}x{video.size[1]}"
        metadata.file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        
        if video.audio:
            metadata.audio_channels = video.audio.nchannels
            metadata.audio_sample_rate = int(video.audio.fps)
        
        video.close()
    except Exception as e:
        print(f"Warning: Could not extract video metadata: {e}")
    
    return metadata


def calculate_rtf(processing_time: float, video_duration: float) -> float:
    """Calculate Real-Time Factor (RTF).
    
    RTF = processing_time / media_duration
    Lower is better (RTF < 1.0 means faster than real-time)
    """
    if video_duration == 0:
        return float('inf')
    return processing_time / video_duration


def run_benchmark(config: BenchmarkConfig) -> BenchmarkResult:
    """Run a single benchmark iteration."""
    print(f"\nRunning benchmark: {config.video_path} -> {config.target_lang}")
    
    result = BenchmarkResult(
        timestamp=datetime.now().isoformat(),
        config=config,
        system_info=get_system_info(),
        video_metadata=get_video_metadata(config.video_path),
        stage_timings=StageTimings(),
        success=False,
    )
    
    profiler = PipelineProfiler(config)
    
    try:
        # Import echolingo
        from echolingo import dub_video
        import whisper
        
        # Warmup iterations
        if config.warmup_iterations > 0:
            print(f"Running {config.warmup_iterations} warmup iteration(s)...")
            for i in range(config.warmup_iterations):
                try:
                    profiler.start_pipeline()
                    model = whisper.load_model("base")
                    output_path = os.path.join(config.output_dir, f"warmup_{i}.mp4")
                    dub_video(
                        video_path=config.video_path,
                        target_lang=config.target_lang,
                        output_path=output_path,
                        captions=config.include_captions,
                        caption_lang=config.caption_lang,
                        whisper_model=model,
                    )
                    profiler.end_pipeline()
                    print(f"  Warmup {i+1}: {profiler.stage_timings.total_pipeline:.2f}s")
                except Exception as e:
                    print(f"  Warmup {i+1} failed: {e}")
        
        # Actual benchmark iteration
        print("Running benchmark iteration...")
        profiler.start_pipeline()
        
        # Load model (stage: video_loading + model_loading)
        profiler.start_stage("video_loading")
        model = whisper.load_model("base")
        profiler.end_stage("video_loading")
        
        # Run pipeline
        output_path = os.path.join(config.output_dir, f"benchmark_{int(time.time())}.mp4")
        dub_video(
            video_path=config.video_path,
            target_lang=config.target_lang,
            output_path=output_path,
            captions=config.include_captions,
            caption_lang=config.caption_lang,
            whisper_model=model,
        )
        
        profiler.end_pipeline()
        
        result.stage_timings = profiler.get_timings()
        result.success = True
        
        print(f"Total pipeline time: {result.stage_timings.total_pipeline:.2f}s")
        rtf = calculate_rtf(result.stage_timings.total_pipeline, result.video_metadata.duration)
        print(f"RTF: {rtf:.2f}")
        
    except Exception as e:
        result.success = False
        result.error_message = str(e)
        print(f"Benchmark failed: {e}")
    
    return result


def run_benchmark_suite(configs: list[BenchmarkConfig]) -> list[BenchmarkResult]:
    """Run multiple benchmarks with different configurations."""
    results = []
    
    for i, config in enumerate(configs, 1):
        print(f"\n{'='*60}")
        print(f"Benchmark {i}/{len(configs)}")
        print(f"{'='*60}")
        
        result = run_benchmark(config)
        results.append(result)
        
        # Save individual result
        result_path = os.path.join(config.output_dir, f"result_{i}.json")
        with open(result_path, 'w') as f:
            json.dump(asdict(result), f, indent=2)
    
    return results


def analyze_results(results: list[BenchmarkResult]) -> dict[str, Any]:
    """Analyze benchmark results and calculate statistics."""
    if not results:
        return {}
    
    successful_results = [r for r in results if r.success]
    if not successful_results:
        return {"error": "No successful benchmark runs"}
    
    stages = [
        "video_loading",
        "audio_extraction", 
        "transcribe",
        "translate",
        "tts_generation",
        "audio_processing",
        "video_composition",
        "total_pipeline"
    ]
    
    analysis = {}
    
    for stage in stages:
        timings = [getattr(r.stage_timings, stage) for r in successful_results]
        if timings:
            timings = [t for t in timings if t > 0]  # Filter out zero times
            if timings:
                analysis[stage] = {
                    "mean": sum(timings) / len(timings),
                    "median": sorted(timings)[len(timings) // 2],
                    "min": min(timings),
                    "max": max(timings),
                    "count": len(timings),
                }
    
    # Calculate RTF statistics
    rtfs = [
        calculate_rtf(r.stage_timings.total_pipeline, r.video_metadata.duration)
        for r in successful_results
    ]
    if rtfs:
        analysis["rtf"] = {
            "mean": sum(rtfs) / len(rtfs),
            "median": sorted(rtfs)[len(rtfs) // 2],
            "min": min(rtfs),
            "max": max(rtfs),
        }
    
    # Success rate
    analysis["success_rate"] = len(successful_results) / len(results)
    
    return analysis


def save_results(results: list[BenchmarkResult], output_path: str) -> None:
    """Save benchmark results to JSON file."""
    data = {
        "results": [asdict(r) for r in results],
        "analysis": analyze_results(results),
        "timestamp": datetime.now().isoformat(),
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")


def main():
    """Main entry point for benchmarking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Echolingo pipeline")
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("--target-lang", default="es", help="Target language code")
    parser.add_argument("--output-dir", default="benchmarks/results", help="Output directory")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations")
    parser.add_argument("--captions", action="store_true", help="Include caption generation")
    parser.add_argument("--caption-lang", default="en", help="Caption language code")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create benchmark configuration
    config = BenchmarkConfig(
        video_path=args.video_path,
        target_lang=args.target_lang,
        output_dir=args.output_dir,
        iterations=args.iterations,
        warmup_iterations=args.warmup,
        include_captions=args.captions,
        caption_lang=args.caption_lang,
    )
    
    # Run benchmarks
    configs = [config] * config.iterations
    results = run_benchmark_suite(configs)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(args.output_dir, f"benchmark_{timestamp}.json")
    save_results(results, output_path)
    
    # Print summary
    analysis = analyze_results(results)
    print(f"\n{'='*60}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"Success rate: {analysis.get('success_rate', 0):.1%}")
    if "total_pipeline" in analysis:
        print(f"Mean total time: {analysis['total_pipeline']['mean']:.2f}s")
        print(f"Median total time: {analysis['total_pipeline']['median']:.2f}s")
    if "rtf" in analysis:
        print(f"Mean RTF: {analysis['rtf']['mean']:.2f}")


if __name__ == "__main__":
    main()
