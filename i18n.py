"""Internationalization - Chinese/English string tables."""

STRINGS = {
    "en": {
        "welcome": (
            "Welcome to Todo Bot!\n\n"
            "I help you manage your tasks. Here are the commands:\n\n"
            "/add <task> - Add a new todo\n"
            "/list - Show pending todos\n"
            "/all - Show all todos\n"
            "/done <id> - Mark as completed\n"
            "/undone <id> - Reopen a todo\n"
            "/del <id> - Delete a todo\n"
            "/edit <id> <new title> - Edit title\n"
            "/note <id> <text> - Add description\n"
            "/priority <id> <1|2|3> - Set priority\n"
            "/due <id> <YYYY-MM-DD> - Set due date\n"
            "/repeat <id> <daily|weekly|monthly|off> - Recurring task\n"
            "/search <keyword> - Search todos\n"
            "/list overdue - Show overdue\n"
            "/list #tag - Filter by tag\n"
            "/assign <id> <user_id> - Assign task (group)\n"
            "/clear - Clear completed\n"
            "/stats - Statistics\n"
            "/export - Export list\n"
            "/lang <en|zh> - Switch language\n"
            "/help - Show this help"
        ),
        "onboarding": (
            "Hi there! I'm Todo Bot - your personal task manager.\n\n"
            "Let's get started! Try adding your first task:"
        ),
        "onboarding_btn": "Add a sample task",
        "onboarding_cmd": "/add My first todo #sample",
        "no_todos": "No todos found. Use /add <task> to create one!",
        "todo_created": "Todo #{id} created!\n\n{title}",
        "todo_completed": "Todo #{id} marked as completed!",
        "todo_reopened": "Todo #{id} reopened!",
        "todo_deleted": "Todo #{id} deleted.",
        "priority_set": "Todo #{id} priority set to {priority}.",
        "due_set": "Todo #{id} due date set to {date}.",
        "title_edited": "Todo #{id} title updated.",
        "note_added": "Todo #{id} description updated.",
        "repeat_set": "Todo #{id} repeat set to {rule}.",
        "repeat_off": "Todo #{id} repeat turned off.",
        "assigned": "Todo #{id} assigned to {name}.",
        "cleared": "Cleared {count} completed todo(s).",
        "search_title": "Search: {keyword}",
        "no_results": "No results found for \"{keyword}\".",
        "pending_todos": "Pending Todos",
        "all_todos": "All Todos",
        "overdue_todos": "Overdue Todos",
        "set_due_prompt": "Set due date for Todo #{id}:\n{title}\n\nOr send /due {id} YYYY-MM-DD",
        "today": "Today",
        "in_3_days": "In 3 days",
        "in_7_days": "In 7 days",
        "back": "Back",
        "done": "Done",
        "reopen": "Reopen",
        "delete": "Delete",
        "undo": "Undo",
        "view_list": "View List",
        "view_all": "View All",
        "view_pending": "View Pending",
        "set_high": "Set High Priority",
        "set_due": "Set Due Date",
        "status": "Status",
        "priority": "Priority",
        "due_date": "Due Date",
        "description": "Description",
        "tags": "Tags",
        "repeat": "Repeat",
        "assignee": "Assignee",
        "completed": "Completed",
        "pending": "Pending",
        "overdue": "OVERDUE",
        "stats_title": "Todo Statistics",
        "total": "Total",
        "export_title": "Todo Export",
        "export_done": "Excel exported:\n{path}",
        "lang_set": "Language set to English.",
        "reminder": "Reminder: Todo #{id} is due today!\n{title}",
        "daily_summary_title": "Daily Summary",
        "daily_summary_text": "You have {pending} pending task(s), {overdue} overdue.",
        # Error messages
        "err_add_usage": "Usage: /add <task title>",
        "err_empty_title": "Task title cannot be empty.",
        "err_done_usage": "Usage: /done <id>",
        "err_undone_usage": "Usage: /undone <id>",
        "err_del_usage": "Usage: /del <id>",
        "err_edit_usage": "Usage: /edit <id> <new title>",
        "err_note_usage": "Usage: /note <id> <text>",
        "err_priority_usage": "Usage: /priority <id> <1|2|3>\n1=High, 2=Medium, 3=Low",
        "err_priority_invalid": "Priority must be 1 (High), 2 (Medium), or 3 (Low).",
        "err_due_usage": "Usage: /due <id> <YYYY-MM-DD>",
        "err_setdue_usage": "Usage: /setdue <id>",
        "err_date_invalid": "Invalid date format. Use YYYY-MM-DD.",
        "err_id_invalid": "Invalid todo ID.",
        "err_not_found": "Todo #{id} not found.",
        "err_search_usage": "Usage: /search <keyword>",
        "err_repeat_usage": "Usage: /repeat <id> <daily|weekly|monthly|off>",
        "err_repeat_invalid": "Rule must be: daily, weekly, monthly, or off.",
        "err_assign_usage": "Usage: /assign <id> <user_id> (group only)",
        "err_assign_private": "Assign only works in group chats.",
        "err_unknown_cmd": "Unknown command. Type /help to see available commands.",
        "err_lang_usage": "Usage: /lang <en|zh>",
    },
    "zh": {
        "welcome": (
            "欢迎使用 Todo Bot！\n\n"
            "我可以帮你管理待办事项，以下是可用命令：\n\n"
            "/add <任务> - 添加待办\n"
            "/list - 查看待办\n"
            "/all - 查看全部\n"
            "/done <编号> - 完成任务\n"
            "/undone <编号> - 重新打开\n"
            "/del <编号> - 删除任务\n"
            "/edit <编号> <新标题> - 修改标题\n"
            "/note <编号> <内容> - 添加备注\n"
            "/priority <编号> <1|2|3> - 设置优先级\n"
            "/due <编号> <YYYY-MM-DD> - 设置截止日期\n"
            "/repeat <编号> <daily|weekly|monthly|off> - 重复任务\n"
            "/search <关键词> - 搜索任务\n"
            "/list overdue - 查看逾期\n"
            "/list #标签 - 按标签筛选\n"
            "/assign <编号> <用户ID> - 指派任务（群聊）\n"
            "/clear - 清除已完成\n"
            "/stats - 统计信息\n"
            "/export - 导出列表\n"
            "/lang <en|zh> - 切换语言\n"
            "/help - 查看帮助"
        ),
        "onboarding": (
            "你好！我是 Todo Bot - 你的个人任务管理助手。\n\n"
            "让我们开始吧！试试添加你的第一个任务："
        ),
        "onboarding_btn": "添加示例任务",
        "onboarding_cmd": "/add 我的第一个待办 #示例",
        "no_todos": "暂无待办事项。使用 /add <任务> 创建一个！",
        "todo_created": "待办 #{id} 已创建！\n\n{title}",
        "todo_completed": "待办 #{id} 已完成！",
        "todo_reopened": "待办 #{id} 已重新打开！",
        "todo_deleted": "待办 #{id} 已删除。",
        "priority_set": "待办 #{id} 优先级已设为 {priority}。",
        "due_set": "待办 #{id} 截止日期已设为 {date}。",
        "title_edited": "待办 #{id} 标题已更新。",
        "note_added": "待办 #{id} 备注已更新。",
        "repeat_set": "待办 #{id} 重复规则已设为 {rule}。",
        "repeat_off": "待办 #{id} 已关闭重复。",
        "assigned": "待办 #{id} 已指派给 {name}。",
        "cleared": "已清除 {count} 个已完成任务。",
        "search_title": "搜索：{keyword}",
        "no_results": "未找到 \"{keyword}\" 的相关结果。",
        "pending_todos": "待办事项",
        "all_todos": "全部任务",
        "overdue_todos": "逾期任务",
        "set_due_prompt": "为待办 #{id} 设置截止日期：\n{title}\n\n或发送 /due {id} YYYY-MM-DD",
        "today": "今天",
        "in_3_days": "3天后",
        "in_7_days": "7天后",
        "back": "返回",
        "done": "完成",
        "reopen": "重新打开",
        "delete": "删除",
        "undo": "撤销",
        "view_list": "查看列表",
        "view_all": "查看全部",
        "view_pending": "查看待办",
        "set_high": "设为高优先级",
        "set_due": "设置截止日期",
        "status": "状态",
        "priority": "优先级",
        "due_date": "截止日期",
        "description": "描述",
        "tags": "标签",
        "repeat": "重复",
        "assignee": "负责人",
        "completed": "已完成",
        "pending": "待办",
        "overdue": "已逾期",
        "stats_title": "任务统计",
        "total": "总计",
        "export_title": "任务导出",
        "export_done": "Excel 已导出：\n{path}",
        "lang_set": "语言已设置为中文。",
        "reminder": "提醒：待办 #{id} 今天截止！\n{title}",
        "daily_summary_title": "每日摘要",
        "daily_summary_text": "你有 {pending} 个待办任务，{overdue} 个已逾期。",
        # Error messages
        "err_add_usage": "用法：/add <任务标题>",
        "err_empty_title": "任务标题不能为空。",
        "err_done_usage": "用法：/done <编号>",
        "err_undone_usage": "用法：/undone <编号>",
        "err_del_usage": "用法：/del <编号>",
        "err_edit_usage": "用法：/edit <编号> <新标题>",
        "err_note_usage": "用法：/note <编号> <内容>",
        "err_priority_usage": "用法：/priority <编号> <1|2|3>\n1=高, 2=中, 3=低",
        "err_priority_invalid": "优先级必须是 1（高）、2（中）或 3（低）。",
        "err_due_usage": "用法：/due <编号> <YYYY-MM-DD>",
        "err_setdue_usage": "用法：/setdue <编号>",
        "err_date_invalid": "日期格式无效，请使用 YYYY-MM-DD。",
        "err_id_invalid": "无效的任务编号。",
        "err_not_found": "待办 #{id} 不存在。",
        "err_search_usage": "用法：/search <关键词>",
        "err_repeat_usage": "用法：/repeat <编号> <daily|weekly|monthly|off>",
        "err_repeat_invalid": "规则必须是：daily、weekly、monthly 或 off。",
        "err_assign_usage": "用法：/assign <编号> <用户ID>（仅群聊）",
        "err_assign_private": "指派任务仅限群聊使用。",
        "err_unknown_cmd": "未知命令。输入 /help 查看可用命令。",
        "err_lang_usage": "用法：/lang <en|zh>",
    },
}

PRIORITY_LABELS_I18N = {
    "en": {1: "High", 2: "Medium", 3: "Low"},
    "zh": {1: "高", 2: "中", 3: "低"},
}

REPEAT_LABELS_I18N = {
    "en": {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"},
    "zh": {"daily": "每天", "weekly": "每周", "monthly": "每月"},
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated string."""
    s = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kwargs:
        s = s.format(**kwargs)
    return s


def priority_label(priority: int, lang: str = "en") -> str:
    return PRIORITY_LABELS_I18N.get(lang, PRIORITY_LABELS_I18N["en"]).get(priority, "Medium")


def repeat_label(rule: str, lang: str = "en") -> str:
    return REPEAT_LABELS_I18N.get(lang, REPEAT_LABELS_I18N["en"]).get(rule, rule)
