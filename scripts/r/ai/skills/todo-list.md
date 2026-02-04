---
description: to-do list and task management
---

You can use the `run_script r/todo_list.py` command for to-do list and task management.

### **1. Add a new task**

```bash
run_script r/todo_list.py add --desc "Finish report" --due "tomorrow"
```

### **2. List active tasks**

```bash
run_script r/todo_list.py list
```

### **3. List all tasks (including closed ones)**

```bash
run_script r/todo_list.py list --all
```

### **4. Search for a task**

```bash
run_script r/todo_list.py search "report"
```

### **5. Edit a task (change status, description, or due date)**

_Replace `1` with the actual ID from the list._

```bash
# Mark as in progress
run_script r/todo_list.py edit 1 --status in_progress

# Mark as closed (done)
run_script r/todo_list.py edit 1 --status closed

# Change description
run_script r/todo_list.py edit 1 --desc "Finish monthly report"
```

### **6. Delete a task**

```bash
run_script r/todo_list.py delete 1
```
