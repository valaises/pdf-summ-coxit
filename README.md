## PDF Summarizer for COXIT

A powerful tool for automated PDF document processing and summarization using LLM models. The tool processes PDF documents, extracts their content, and generates structured summaries using advanced language models.

Note: Tool is specifically designed for COXIT documents and won't be of use for generic PDF documents.
## Features

- 📄 Automated PDF document processing
- 🔍 Intelligent section detection and organization
- 🤖 LLM-powered content summarization
- 📊 Structured output in CSV format
- 👀 Real-time document monitoring
- 🚀 Multi-threaded processing pipeline

## On-Device Installation & Usage
1. Install uv

[about: uv - modern pip, pipx, poetry, venv replacement](https://docs.astral.sh/uv/getting-started/installation/)
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

2. Clone the repository
```bash
git clone https://github.com/valaises/pdf-summ-coxit.git
```

3. Run the installation script
```bash
sh scripts/install.sh
```

4. Set environmental variables
```bash
cp .env.example .env
```

```bash
#.env

GEMINI_API_KEY =
OPENAI_API_KEY = 
```
```
source .env
```

5. Run the summarizer
```bash
uv run src/core/main.py -d /path/to/your/pdfs
```

6. Place your PDF documents in a target directory e.g.
```
cp documents/* /path/to/your/pdfs
```

### Command Line Arguments

- `-d` `--target-dir`: Directory to monitor for PDF files (required)
- `--debug`: Enable debug logging (optional)

## How It Works

#### The tool operates in a pipeline:

1. **Document Monitoring**: Watches the target directory for new PDF files
2. **PDF Processing**: Extracts and processes text from PDF documents
3. **Step 1**: Initial content analysis and section detection
4. **Step 2**: Section-based summarization
5. **Output Formatting**: Generates structured CSV output


## Getting results

After each document is processed, `output.csv` and `output_parts.csv` are automatically re-generated in a directory specified by the `-d` `--output_dir` argument.