import os
import re

def clean_markdown(content: str) -> str:
    # Remove bold markdown (**text** → text)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)

    # Remove horizontal rules (---)
    content = re.sub(r'\n?[-]{3,}\n?', '\n', content)

    # Normalize multiple blank lines
    content = re.sub(r'\n{2,}', '\n\n', content)

    return content.strip()

input_folder = "video_reports"
output_folder = "video_reports_new"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".md"):
        in_path = os.path.join(input_folder, filename)
        out_path = os.path.join(output_folder, filename)

        with open(in_path, 'r', encoding='utf-8') as f:
            raw = f.read()
            cleaned = clean_markdown(raw)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)

        print(f"Cleaned and saved: {filename}")
