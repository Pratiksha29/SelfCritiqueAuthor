"""Main entry point script for the EHR audit pipeline."""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from self_critique_author.core.pipeline import EHRPipeline
from self_critique_author.utils.config import Config
from self_critique_author.utils.logger import setup_logging


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="EHR Data Auditor with WhatsApp Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with 5 records (demo)
  python run_pipeline.py --demo 5
  
  # Run full pipeline with all records
  python run_pipeline.py
  
  # Run specific steps
  python run_pipeline.py --step audit --demo 5
  python run_pipeline.py --step verify
  python run_pipeline.py --step resolve
  
  # Custom configuration
  python run_pipeline.py --config custom_settings.yaml
        """
    )
    
    # Input arguments
    parser.add_argument(
        "--input", "-i",
        default="data/raw/ehr_messy.json",
        help="Input data file path (default: data/raw/ehr_messy.json)"
    )
    
    # Mode arguments
    parser.add_argument(
        "--demo", "-d",
        type=int,
        nargs="?",
        const=5,
        default=0,
        metavar="N",
        help="Run with N records only (default: 5 if no number specified)"
    )
    
    parser.add_argument(
        "--step", "-s",
        choices=["audit", "verify", "resolve"],
        help="Run specific pipeline step only"
    )
    
    # Configuration arguments
    parser.add_argument(
        "--config", "-c",
        help="Configuration file path (default: config/settings.yaml)"
    )
    
    parser.add_argument(
        "--no-verification",
        action="store_true",
        help="Skip verification step"
    )
    
    # Output arguments
    parser.add_argument(
        "--output", "-o",
        help="Output directory path"
    )
    
    # Logging arguments
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config(args.config) if args.config else Config()
        
        # Override config with command line arguments
        if args.log_level:
            config.logging.level = args.log_level
        
        if args.verbose:
            config.logging.level = "DEBUG"
        
        if args.no_verification:
            config.verification.whatsapp_enabled = False
            config.verification.doctor_enabled = False
        
        if args.output:
            config.storage.output_directory = args.output
        
        # Setup logging
        setup_logging(config.logging.__dict__)
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Create and run pipeline
    try:
        pipeline = EHRPipeline(config)
        
        print(f"🚀 Starting EHR Audit Pipeline v{config.app.version}")
        print(f"📁 Input: {args.input}")
        
        if args.demo:
            print(f"🎯 Demo mode: {args.demo} records")
        
        if args.step:
            print(f"🔧 Running step: {args.step}")
        
        print("-" * 50)
        
        # Run pipeline
        if args.step:
            # Run specific step
            results = pipeline.run_step(
                step=args.step,
                input_data_path=args.input,
                demo_mode=args.demo > 0,
                demo_count=args.demo
            )
        else:
            # Run full pipeline
            results = pipeline.run(
                input_data_path=args.input,
                demo_mode=args.demo > 0,
                demo_count=args.demo
            )
        
        # Display results
        print("-" * 50)
        print("✅ Pipeline completed successfully!")
        
        if "summary" in results:
            summary = results["summary"]
            print(f"\n📊 Summary:")
            print(f"   Total patients: {summary['patient_statistics']['total_patients']}")
            print(f"   Consistency rate: {summary['patient_statistics']['consistency_rate']:.1%}")
            print(f"   Total inconsistencies: {summary['grievance_statistics']['total_inconsistencies']}")
            print(f"   Processing time: {summary['execution_time']['total_processing_time_ms'] / 1000:.1f}s")
        
        if "output_paths" in results:
            print(f"\n📁 Output files:")
            for name, path in results["output_paths"].items():
                print(f"   {name}: {path}")
        
        print(f"\n🎉 Done!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
