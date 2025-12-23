# Task Tracker MCP Server

A comprehensive task tracking and management system accessible via the **Model Context Protocol (MCP)**. Features projects, tags, priorities, full-text search, and analytics—all designed to work seamlessly with Claude Code and other MCP-compatible tools.

## Features

✅ **Task Management**: Create, update, delete, and track tasks with priorities and due dates
✅ **Projects**: Organize tasks into projects
✅ **Tags**: Categorize and filter tasks with custom tags
✅ **Full-Text Search**: Search across task titles and descriptions
✅ **Analytics**: View completion rates, overdue tasks, and productivity metrics
✅ **SQLite Backend**: Local data storage with FTS5 full-text search
✅ **Configurable Port**: Run on any available port
✅ **Docker Support**: Easy containerization and deployment
✅ **Cross-Platform**: Works on Windows, Linux, macOS, and WSL

## Quick Start

### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/yoshiwatanabe/task-tracker-mcp.git
cd task-tracker-mcp

# Install in development mode
pip install -e .

# Run the server
python -m task_tracker_mcp.server
```

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or manually build and run
docker build -t task-tracker:latest .
docker run -p 8000:8000 task-tracker:latest
```

### Option 3: Custom Port

```bash
# Local with custom port
TASK_TRACKER_MCP_PORT=9000 python -m task_tracker_mcp.server

# Docker with custom port
docker run -e TASK_TRACKER_MCP_PORT=9000 -p 9000:9000 task-tracker:latest

# Docker Compose with custom port
# Edit docker-compose.yml, update TASK_TRACKER_MCP_PORT and ports
docker-compose up -d
```

## Configuration

### Environment Variables

- `TASK_TRACKER_MCP_PORT` (default: `8000`) - Port the server listens on
- `PYTHONUNBUFFERED` (default: `1`) - Show Python logs in real-time

### Database

- **Location**: `tasks.db` (created automatically in current directory)
- **Type**: SQLite with FTS5 full-text search
- **Schema**: Includes tables for tasks, projects, tags, and relationships

## MCP Server Tools

The server exposes 35+ tools for task management:

### Task Operations
- `create_task` - Create new task
- `get_task` - Get task by ID
- `list_tasks` - List all tasks with pagination
- `update_task` - Update task properties
- `delete_task` - Delete task
- `search_tasks` - Full-text search
- `filter_tasks` - Filter by status, priority, project, or tag

### Project Operations
- `create_project` - Create project
- `get_project` - Get project details
- `list_projects` - List all projects
- `update_project` - Update project
- `delete_project` - Delete project
- `get_project_tasks` - Get tasks for a project

### Tag Management
- `add_tag` - Add tag to task
- `remove_tag` - Remove tag from task
- `list_tags` - List all tags

### Analytics
- `task_statistics` - Get task statistics
- `get_overdue_tasks` - Get overdue tasks

### Resources
- `task://all` - All tasks
- `task://pending` - Pending tasks
- `task://high-priority` - High-priority tasks
- `project://all` - All projects
- `stats://summary` - Statistics summary

### Prompts (Workflows)
- `daily-review` - Daily task review workflow
- `weekly-planning` - Weekly planning workflow
- `project-summary` - Project summary (with project_id parameter)
- `overdue-analysis` - Overdue tasks analysis

## Integration with Claude Code

### 1. Using with `.mcp.json`

In your Claude Code project, create `.mcp.json`:

```json
{
  "mcpServers": {
    "task-tracker": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "task_tracker_mcp.server"]
    }
  }
}
```

Or for HTTP-based access (with additional setup):

```json
{
  "mcpServers": {
    "task-tracker": {
      "type": "http",
      "url": "http://localhost:8000"
    }
  }
}
```

### 2. Using with Skills

Create a skill in `.github/skills/task-organizer/SKILL.md` that references this server:

```yaml
---
name: task-organizer
description: Track and manage tasks using the task-tracker MCP server
---

# Task Organizer Skill

This skill provides task management capabilities via the task-tracker MCP server...
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Architecture

```
task-tracker-mcp/
├── src/task_tracker_mcp/
│   ├── __init__.py
│   ├── server.py              # FastMCP server with tool definitions
│   ├── database.py            # SQLite database operations
│   └── schema.sql             # Database schema
├── tests/
│   └── test_server.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Database Schema

### Tasks Table
- `id` - Primary key
- `title` - Task title (required)
- `description` - Task description
- `status` - pending, in_progress, completed, blocked
- `priority` - low, medium, high
- `project_id` - Associated project
- `due_date` - Due date (YYYY-MM-DD format)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Projects Table
- `id` - Primary key
- `name` - Project name
- `description` - Project description
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Tags Table
- `id` - Primary key
- `name` - Tag name
- `task_id` - Associated task

## Performance Notes

- **Full-Text Search**: Uses FTS5 for fast text searching
- **Pagination**: Default limit of 50 items, supports custom offset
- **Database**: SQLite with async support (aiosqlite)
- **Concurrency**: Handles concurrent requests with async/await

## Deployment Options

### Local Development
```bash
python -m task_tracker_mcp.server
```

### Docker Container
```bash
docker run -p 8000:8000 your-username/task-tracker:latest
```

### Kubernetes / Cloud
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: task-tracker
spec:
  containers:
  - name: task-tracker
    image: your-username/task-tracker:latest
    ports:
    - containerPort: 8000
    env:
    - name: TASK_TRACKER_MCP_PORT
      value: "8000"
```

## Troubleshooting

### Port Already in Use
```bash
# Check which process is using the port
lsof -i :8000

# Use different port
TASK_TRACKER_MCP_PORT=9000 python -m task_tracker_mcp.server
```

### Permission Denied (Docker)
```bash
# Ensure Docker is running
docker ps

# Check Docker daemon
sudo systemctl start docker
```

### Database Locked
```bash
# This usually indicates concurrent access issues
# Restart the server and ensure only one instance is running
```

## Cross-Platform Usage

### Windows (Native)
```cmd
python -m task_tracker_mcp.server
```

### Windows (Docker Desktop)
```bash
docker run -p 8000:8000 task-tracker:latest
```

### WSL2 (Ubuntu)
```bash
# Access Windows Docker from WSL
docker run -p 8000:8000 task-tracker:latest

# Or access Windows server from WSL
python -m task_tracker_mcp.server  # on Windows
# Then in WSL: use http://host.docker.internal:8000 or Windows IP
```

### macOS / Linux
```bash
python -m task_tracker_mcp.server
# or
docker run -p 8000:8000 task-tracker:latest
```

## Dependencies

- **mcp** >= 1.1.2 - Model Context Protocol
- **aiosqlite** >= 0.20.0 - Async SQLite support
- **Python** >= 3.11

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Roadmap

- [ ] HTTP/SSE transport support
- [ ] PostgreSQL backend option
- [ ] Multi-user support
- [ ] Time tracking
- [ ] Recurring tasks
- [ ] Task templates
- [ ] Integrations (Slack, Discord, etc.)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Ready to use?** Start with the Quick Start section above, or integrate with Claude Code using the configuration examples provided.
