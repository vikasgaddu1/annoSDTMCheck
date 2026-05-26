"""Test script for textbox annotation auto-resize functionality.

This script tests the automatic resizing of PDF textbox annotations
to ensure text content is fully visible without wrapping or truncation.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sdtm_checker.core.text_dimension_calculator import TextDimensionCalculator
from sdtm_checker.core.annotation_resizer import AnnotationResizer


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test textbox annotation auto-resize functionality'
    )
    parser.add_argument(
        'input_pdf',
        help='Path to input PDF file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output PDF file (default: input_resized.pdf)',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Detect and report without modifying PDF'
    )
    parser.add_argument(
        '--expand-width',
        action='store_true',
        default=True,
        help='Allow expanding annotation width (default: True)'
    )
    parser.add_argument(
        '--no-expand-width',
        action='store_false',
        dest='expand_width',
        help='Do not expand annotation width'
    )
    parser.add_argument(
        '--expand-height',
        action='store_true',
        default=True,
        help='Allow expanding annotation height (default: True)'
    )
    parser.add_argument(
        '--no-expand-height',
        action='store_false',
        dest='expand_height',
        help='Do not expand annotation height'
    )
    parser.add_argument(
        '--max-width-expansion',
        type=float,
        default=200.0,
        help='Maximum width expansion in points (default: 200)'
    )
    parser.add_argument(
        '--max-height-expansion',
        type=float,
        default=300.0,
        help='Maximum height expansion in points (default: 300)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate input file
    if not os.path.exists(args.input_pdf):
        logger.error(f"Input PDF not found: {args.input_pdf}")
        return 1
    
    # Determine output path
    if args.output is None:
        input_path = Path(args.input_pdf)
        args.output = str(input_path.parent / f"{input_path.stem}_resized.pdf")
    
    logger.info("=" * 80)
    logger.info("TEXTBOX ANNOTATION AUTO-RESIZE TEST")
    logger.info("=" * 80)
    logger.info(f"Input PDF: {args.input_pdf}")
    logger.info(f"Output PDF: {args.output}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Expand width: {args.expand_width}")
    logger.info(f"Expand height: {args.expand_height}")
    logger.info(f"Max width expansion: {args.max_width_expansion} points")
    logger.info(f"Max height expansion: {args.max_height_expansion} points")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        # Create calculator and resizer
        calculator = TextDimensionCalculator()
        resizer = AnnotationResizer(
            calculator=calculator,
            expand_width=args.expand_width,
            expand_height=args.expand_height,
            max_width_expansion=args.max_width_expansion,
            max_height_expansion=args.max_height_expansion
        )
        
        # Process PDF
        logger.info("Processing PDF...")
        stats = resizer.resize_annotations(
            pdf_path=args.input_pdf,
            output_path=args.output if not args.dry_run else None,
            dry_run=args.dry_run
        )
        
        # Generate and print report
        report = resizer.generate_report(stats)
        print("\n" + report)
        
        if not args.dry_run:
            logger.info(f"\n✓ Successfully saved resized PDF to: {args.output}")
        else:
            logger.info(f"\n✓ Dry run complete - no changes made")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

