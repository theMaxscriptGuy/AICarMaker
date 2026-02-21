# AICarMaker

A simple Gemini-powered car render generator based on blueprint/reference files.

## Features

- Project name
- Gemini API key input
- Default Gemini model: `gemini-2.5-flash-image`
- Drag & drop car blueprint files (png/jpg/webp/pdf)
- Prompt box to describe the car
- Camera angles (drag & drop a `.txt` of angles, or add manually)
- Generate renders (one image per camera angle)

## Run (dev)

```bash
cd AICarMaker
pip install -e ".[gemini]"
aicarmaker
```

Output images are written to `output/<project>/<timestamp>/`.
