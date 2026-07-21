import os

def search_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'dfs' in content.lower() or 'stack' in content.lower() or 'lifo' in content.lower():
                            print(f"Match found in: {path}")
                            # Print first 200 chars
                            print(content[:200])
                            print("-" * 40)
                except Exception as e:
                    pass

search_files("c:\\Users\\Dell\\Documents")
