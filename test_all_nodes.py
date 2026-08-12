import os
import subprocess
import glob
from pathlib import Path

def main():
    project_root = r"c:\Users\majip\Downloads\rl-jepa-car ai\AGRO_AI_PROJECT"
    
    # Directories to search
    search_dirs = [
        "core",
        "machines",
        "training/scripts"
    ]
    
    test_results = []
    
    print("Finding python files to test...")
    python_files = []
    for d in search_dirs:
        full_dir = os.path.join(project_root, d)
        for root, _, files in os.walk(full_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__init__"):
                    filepath = os.path.join(root, file)
                    # Check if it has a main block
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if "if __name__ == '__main__':" in f.read():
                            python_files.append(filepath)
                            
    print(f"Found {len(python_files)} executable nodes/scripts.")
    
    report_lines = [
        "# AGRO-AI Comprehensive Testing Report",
        "",
        "The following report details the mock-execution results for all executable Python nodes and training scripts in the codebase. Since `rclpy` is not present in this testing environment, all nodes gracefully fall back to their offline mock routines to verify structural and syntax integrity.",
        ""
    ]
    
    success_count = 0
    fail_count = 0
    
    for py_file in python_files:
        rel_path = os.path.relpath(py_file, project_root)
        print(f"Testing {rel_path}...")
        
        try:
            # Run the script with a timeout to prevent infinite hangs just in case
            result = subprocess.run(
                ["python", py_file],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                status = "✅ PASS"
                success_count += 1
            else:
                status = "❌ FAIL"
                fail_count += 1
                
            report_lines.append(f"## {rel_path} - {status}")
            report_lines.append("```text")
            report_lines.append(result.stdout.strip())
            if result.stderr.strip():
                report_lines.append("--- STDERR ---")
                report_lines.append(result.stderr.strip())
            report_lines.append("```")
            report_lines.append("")
            
        except subprocess.TimeoutExpired:
            report_lines.append(f"## {rel_path} - ⚠️ TIMEOUT")
            report_lines.append("```text\nScript timed out after 10 seconds.\n```\n")
            fail_count += 1
        except Exception as e:
            report_lines.append(f"## {rel_path} - ❌ ERROR")
            report_lines.append(f"```text\n{str(e)}\n```\n")
            fail_count += 1

    summary = f"### Summary\n- **Total Scripts Tested**: {len(python_files)}\n- **Passed**: {success_count}\n- **Failed**: {fail_count}\n"
    report_lines.insert(4, summary)
    
    report_path = os.path.join(project_root, "docs", "14_TESTING_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Testing complete. Report generated at {report_path}")

if __name__ == "__main__":
    main()
