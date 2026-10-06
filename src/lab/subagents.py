"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use this subagent to explore the workspace, read specifications, documentation, and source code, "
                "inspect data samples, log files, and test failures, and summarize findings. "
                "Do NOT use this subagent to modify or write files."
            ),
            "system_prompt": (
                "You are an engineering explorer subagent. Your sole responsibility is to investigate the workspace, "
                "read files, inspect data formats, and provide comprehensive, factual reports back to the main agent. "
                "Do NOT edit, write, or delete any files."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use this subagent to implement specific bug fixes, perform data cleaning, parse logs, "
                "run shell commands, execute scripts, and verify fixes with tests. "
                "Call this subagent when concrete file edits or command executions are needed."
            ),
            "system_prompt": (
                "You are an engineering implementer subagent. Your responsibility is to execute code modifications, "
                "clean datasets, write required output files, run tests and scripts using the shell, and report back "
                "the exact changes made and execution results."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use this subagent to independently audit, verify, and sanity-check results against all instructions "
                "and hidden constraints (such as edge cases, timezones, formatting conventions, and duplicate entries) "
                "before finalizing the task. Do NOT use to edit files."
            ),
            "system_prompt": (
                "You are an independent reviewer subagent. Your responsibility is to inspect modified files and "
                "generated outputs, verify compliance against instructions and edge cases, identify any remaining "
                "discrepancies or broken rules, and report your audit findings back to the main agent without making edits."
            ),
        },
    ]
