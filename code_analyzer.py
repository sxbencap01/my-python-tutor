import sys
import io
import ast
from typing import Dict, Any, Tuple

class CodeAnalyzer:
    def __init__(self):
        pass

    def run_code(self, code: str) -> Tuple[str, str]:
        """
        Executes the provided Python code and captures the output.
        Returns a tuple of (output, error).
        """
        # Create a string buffer to capture stdout
        stdout_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buffer

        error = ""
        output = ""

        try:
            # Use a dictionary to store global and local variables for execution
            # This provides a clean environment for each run
            exec_globals = {}
            exec(code, exec_globals)
        except Exception as e:
            error = str(e)
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            output = stdout_buffer.getvalue()

        return output, error

    def analyze_structure(self, code: str) -> Dict[str, Any]:
        """
        Uses the AST to analyze the code structure.
        """
        try:
            tree = ast.parse(code)
            analysis = {
                "has_loops": False,
                "has_functions": False,
                "has_classes": False,
                "imports": [],
                "variable_count": 0,
                "comments_count": 0
            }

            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    analysis["has_loops"] = True
                elif isinstance(node, ast.FunctionDef):
                    analysis["has_functions"] = True
                elif isinstance(node, ast.ClassDef):
                    analysis["has_classes"] = True
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name in node.names if isinstance(node, ast.Import) else [node]:
                        if hasattr(name, 'name'):
                            analysis["imports"].append(name.name)
                        elif hasattr(node, 'module'):
                            analysis["imports"].append(node.module)
                elif isinstance(node, ast.Assign):
                    analysis["variable_count"] += len(node.targets)

            # Count comments manually as ast.parse doesn't include them easily without extra effort
            analysis["comments_count"] = len([line for line in code.split('\n') if line.strip().startswith('#')])

            return analysis
        except SyntaxError as e:
            return {"error": f"Syntax Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Analysis Error: {str(e)}"}

# Example usage (commented out)
# if __name__ == "__main__":
#     analyzer = CodeAnalyzer()
#     code = "for i in range(5):\n    print(i)\n# This is a comment"
#     out, err = analyzer.run_code(code)
#     print(f"Output: {out}")
#     print(f"Analysis: {analyzer.analyze_structure(code)}")
