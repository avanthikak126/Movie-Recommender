import glob
import os

for f in glob.glob('**/*.py', recursive=True):
    if os.path.isfile(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        new_content = content.replace('width="stretch"', 'width="stretch"')
        new_content = new_content.replace('width="content"', 'width="content"')
        
        if content != new_content:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
                print(f"Updated {f}")
