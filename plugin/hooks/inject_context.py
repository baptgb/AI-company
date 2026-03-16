#!/usr/bin/env python3
"""SubagentStart Hook - Inject CLAUDE.md and OS registration guidance into subagents.
stdout content is injected as additionalContext into the subagent context.
"""

import json
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    claude_md = project_root / "CLAUDE.md"

    output = ""

    # Inject CLAUDE.md core content
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            if content:
                output += "=== AI Team OS \u9879\u76ee\u6307\u4ee4 ===\n"
                output += content
                output += "\n"
        except OSError:
            pass

    # Inject OS registration guidance
    output += """
=== AI Team OS \u81ea\u52a8\u6ce8\u518c\u6307\u5f15 ===
\u4f60\u6b63\u5728\u4e00\u4e2a\u914d\u7f6e\u4e86AI Team OS\u7684\u9879\u76ee\u4e2d\u5de5\u4f5c\u3002\u8bf7\u5728\u5f00\u59cb\u5de5\u4f5c\u524d\uff1a
1. \u4f7f\u7528MCP tool: os_health_check \u68c0\u67e5OS\u662f\u5426\u53ef\u7528
2. \u5982\u679c\u53ef\u7528\uff0c\u4f7f\u7528MCP tool: team_list \u67e5\u770b\u73b0\u6709\u56e2\u961f
3. \u4f7f\u7528MCP tool: agent_register \u6ce8\u518c\u81ea\u5df1\u5230\u56e2\u961f
4. \u6ce8\u518c\u540e\u9605\u8bfb\u8fd4\u56de\u7684team_snapshot\u4e86\u89e3\u56e2\u961f\u72b6\u6001
\u5982\u679cOS\u4e0d\u53ef\u7528\uff0c\u8df3\u8fc7\u6ce8\u518c\uff0c\u6b63\u5e38\u6267\u884c\u4f60\u7684\u4efb\u52a1\u3002"""

    # Output JSON format (CC requires hookSpecificOutput format)
    json_output = json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": output,
            }
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    sys.stdout.write(json_output)


if __name__ == "__main__":
    main()
