# Paper to Slides

Convert academic papers (PDF) into presentation slides using Google's Gemini AI.

## Overview

This project automatically converts academic papers in PDF format into presentation slides. It leverages Google's Gemini API to:
- Analyze PDF documents and extract key information
- Generate visually appealing slides with consistent styling
- Maintain visual consistency across all slides using reference images
- Integrate figures from the original paper into relevant slides

## Features

- **PDF Analysis**: Extract text, metadata, and images from academic papers
- **Intelligent Content Planning**: Create a structured presentation plan based on paper content
- **Visual Consistency**: Generate slides with consistent styling using reference images
- **Image Integration**: Incorporate relevant figures from the original paper
- **Caching**: Cache intermediate results to speed up processing
- **Configurable**: Highly configurable via JSON configuration files

## Requirements

- Python 3.10+
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd paper-to-slides
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

Generate slides from a PDF paper:
```bash
python scripts/generate_slides.py --pdf path/to/paper.pdf --output output_directory/
```

To disable caching:
```bash
python scripts/generate_slides.py --pdf path/to/paper.pdf --output output_directory/ --no-cache
```

## Architecture

The system is organized into several modules:

- `pdf`: Extract text and images from PDF files
- `llm`: Interface with Gemini API for document analysis and image generation
- `presentation`: Plan presentation structure and coordinate slide generation
- `output`: Save generated slides and metadata
- `utils`: Common utilities like configuration loading, logging, and caching

## Configuration

The system can be configured via:
- `config/config.json`: Main configuration
- `config/image_generation_config.json`: Image generation settings
- Environment variables in `.env`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT