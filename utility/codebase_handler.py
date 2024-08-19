import os

class CodeHelper:
    def __init__(self):
        self.supported_extensions = ('.py', '.js', '.html', '.css', '.tsx', '.ts', '.json')

    def get_code_files(self, path):
        code_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(self.supported_extensions):
                    code_files.append(os.path.join(root, file))
        print(code_files)
        return code_files

    def read_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def analyze_codebase(self, path):
        try:
            code_files = self.get_code_files(path)
            if not code_files:
                return f"No supported code files found in the directory: {path}"
            codebase_content = ""
            for file in code_files:
                content = self.read_file_content(file)
                codebase_content += f"File: {file}\n\n{content}\n\n"
            return codebase_content
        except Exception as e:
            return f"Error analyzing codebase: {str(e)}"