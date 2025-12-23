#!/usr/bin/env python3
"""FastMCP server for task tracking system."""

import asyncio
import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(name="task-tracker")

# Initialize database manager
db_manager = DatabaseManager("tasks.db")


# ==================== TOOLS ====================


@mcp.tool()
async def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    status: str = "pending",
    project_id: int = None,
    due_date: str = None,
) -> str:
    """Create a new task.

    Args:
        title: Task title (required)
        description: Task description
        priority: Priority level (low, medium, high)
        status: Task status (pending, in_progress, completed, blocked)
        project_id: Associated project ID
        due_date: Due date in YYYY-MM-DD format
    """
    try:
        task = await db_manager.create_task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            project_id=project_id,
            due_date=due_date,
        )
        return json.dumps(task, indent=2)
    except Exception as e:
        return f"Error creating task: {str(e)}"


@mcp.tool()
async def get_task(task_id: int) -> str:
    """Get a task by ID."""
    try:
        task = await db_manager.get_task(task_id)
        if not task:
            return f"Task {task_id} not found"
        return json.dumps(task, indent=2)
    except Exception as e:
        return f"Error getting task: {str(e)}"


@mcp.tool()
async def list_tasks(limit: int = 50, offset: int = 0) -> str:
    """List all tasks with pagination."""
    try:
        tasks = await db_manager.list_tasks(limit=limit, offset=offset)
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"


@mcp.tool()
async def update_task(task_id: int, **kwargs) -> str:
    """Update a task by ID.

    Supported fields: title, description, status, priority, due_date
    """
    try:
        task = await db_manager.update_task(task_id, **kwargs)
        if not task:
            return f"Task {task_id} not found"
        return json.dumps(task, indent=2)
    except Exception as e:
        return f"Error updating task: {str(e)}"


@mcp.tool()
async def delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    try:
        success = await db_manager.delete_task(task_id)
        if success:
            return f"Task {task_id} deleted successfully"
        return f"Failed to delete task {task_id}"
    except Exception as e:
        return f"Error deleting task: {str(e)}"


@mcp.tool()
async def search_tasks(query: str) -> str:
    """Search tasks using full-text search."""
    try:
        if not query or len(query.strip()) < 2:
            return "Search query too short (minimum 2 characters)"
        tasks = await db_manager.search_tasks(query)
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error searching tasks: {str(e)}"


@mcp.tool()
async def filter_tasks(**filters) -> str:
    """Filter tasks by various criteria.

    Supported filters: status, priority, project_id, tag_name
    """
    try:
        tasks = await db_manager.filter_tasks(**filters)
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error filtering tasks: {str(e)}"


# ==================== PROJECT OPERATIONS ====================


@mcp.tool()
async def create_project(name: str, description: str = "") -> str:
    """Create a new project."""
    try:
        project = await db_manager.create_project(name, description)
        return json.dumps(project, indent=2)
    except Exception as e:
        return f"Error creating project: {str(e)}"


@mcp.tool()
async def get_project(project_id: int) -> str:
    """Get a project by ID."""
    try:
        project = await db_manager.get_project(project_id)
        if not project:
            return f"Project {project_id} not found"
        return json.dumps(project, indent=2)
    except Exception as e:
        return f"Error getting project: {str(e)}"


@mcp.tool()
async def list_projects() -> str:
    """List all projects."""
    try:
        projects = await db_manager.list_projects()
        return json.dumps({"count": len(projects), "projects": projects}, indent=2)
    except Exception as e:
        return f"Error listing projects: {str(e)}"


@mcp.tool()
async def update_project(project_id: int, **kwargs) -> str:
    """Update a project."""
    try:
        project = await db_manager.update_project(project_id, **kwargs)
        if not project:
            return f"Project {project_id} not found"
        return json.dumps(project, indent=2)
    except Exception as e:
        return f"Error updating project: {str(e)}"


@mcp.tool()
async def delete_project(project_id: int) -> str:
    """Delete a project."""
    try:
        success = await db_manager.delete_project(project_id)
        if success:
            return f"Project {project_id} deleted successfully"
        return f"Failed to delete project {project_id}"
    except Exception as e:
        return f"Error deleting project: {str(e)}"


@mcp.tool()
async def get_project_tasks(project_id: int) -> str:
    """Get all tasks for a project."""
    try:
        tasks = await db_manager.get_project_tasks(project_id)
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error getting project tasks: {str(e)}"


# ==================== TAG OPERATIONS ====================


@mcp.tool()
async def add_tag(task_id: int, tag_name: str) -> str:
    """Add a tag to a task."""
    try:
        success = await db_manager.add_tag(task_id, tag_name)
        if success:
            task = await db_manager.get_task(task_id)
            return json.dumps(task, indent=2)
        return f"Failed to add tag to task {task_id}"
    except Exception as e:
        return f"Error adding tag: {str(e)}"


@mcp.tool()
async def remove_tag(task_id: int, tag_name: str) -> str:
    """Remove a tag from a task."""
    try:
        success = await db_manager.remove_tag(task_id, tag_name)
        if success:
            task = await db_manager.get_task(task_id)
            return json.dumps(task, indent=2)
        return f"Failed to remove tag from task {task_id}"
    except Exception as e:
        return f"Error removing tag: {str(e)}"


@mcp.tool()
async def list_tags() -> str:
    """List all tags."""
    try:
        tags = await db_manager.list_tags()
        return json.dumps({"count": len(tags), "tags": tags}, indent=2)
    except Exception as e:
        return f"Error listing tags: {str(e)}"


# ==================== ANALYTICS OPERATIONS ====================


@mcp.tool()
async def task_statistics() -> str:
    """Get task statistics."""
    try:
        stats = await db_manager.get_task_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error getting statistics: {str(e)}"


@mcp.tool()
async def get_overdue_tasks() -> str:
    """Get all overdue tasks."""
    try:
        tasks = await db_manager.get_overdue_tasks()
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error getting overdue tasks: {str(e)}"


# ==================== RESOURCES ====================


@mcp.resource("task://all")
async def all_tasks_resource() -> str:
    """Access all tasks as a resource."""
    try:
        tasks = await db_manager.list_tasks(limit=1000)
        return json.dumps({"tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error retrieving tasks: {str(e)}"


@mcp.resource("task://pending")
async def pending_tasks_resource() -> str:
    """Access pending tasks as a resource."""
    try:
        tasks = await db_manager.filter_tasks(status="pending")
        return json.dumps({"tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error retrieving pending tasks: {str(e)}"


@mcp.resource("task://high-priority")
async def high_priority_tasks_resource() -> str:
    """Access high-priority tasks as a resource."""
    try:
        tasks = await db_manager.filter_tasks(priority="high")
        return json.dumps({"tasks": tasks}, indent=2)
    except Exception as e:
        return f"Error retrieving high-priority tasks: {str(e)}"


@mcp.resource("project://all")
async def all_projects_resource() -> str:
    """Access all projects as a resource."""
    try:
        projects = await db_manager.list_projects()
        return json.dumps({"projects": projects}, indent=2)
    except Exception as e:
        return f"Error retrieving projects: {str(e)}"


@mcp.resource("stats://summary")
async def stats_summary_resource() -> str:
    """Access task statistics summary as a resource."""
    try:
        stats = await db_manager.get_task_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error retrieving statistics: {str(e)}"


# ==================== PROMPTS ====================


@mcp.prompt()
async def daily_review() -> str:
    """Prompt: Daily task review workflow."""
    try:
        tasks = await db_manager.filter_tasks(status="pending")
        overdue = await db_manager.get_overdue_tasks()
        stats = await db_manager.get_task_statistics()

        prompt = f"""# Daily Task Review

## Summary
- Total tasks: {stats.get('total', 0)}
- Completed: {stats.get('completed', 0)}
- Pending: {stats.get('pending', 0)}
- Overdue: {len(overdue)}

## Overdue Tasks ({len(overdue)})
"""
        for task in overdue:
            prompt += f"- [{task.get('priority')}] {task.get('title')} (due: {task.get('due_date')})\n"

        prompt += "\n## Today's Pending Tasks\n"
        for task in tasks[:10]:
            prompt += f"- [{task.get('priority')}] {task.get('title')}\n"

        return prompt
    except Exception as e:
        return f"Error generating daily review: {str(e)}"


@mcp.prompt()
async def weekly_planning() -> str:
    """Prompt: Weekly planning workflow."""
    try:
        projects = await db_manager.list_projects()
        stats = await db_manager.get_task_statistics()

        prompt = f"""# Weekly Planning

## Project Overview
Projects: {len(projects)}

## Task Metrics
- Total: {stats.get('total', 0)}
- Completed this week: {stats.get('completed', 0)}
- Completion rate: {stats.get('completion_rate', 0):.1f}%
- High priority: {stats.get('high_priority', 0)}

## Projects
"""
        for project in projects:
            tasks = await db_manager.get_project_tasks(project.get("id"))
            prompt += f"- {project.get('name')}: {len(tasks)} tasks\n"

        return prompt
    except Exception as e:
        return f"Error generating weekly planning: {str(e)}"


@mcp.prompt()
async def project_summary_prompt(project_id: int) -> str:
    """Prompt: Project summary workflow."""
    try:
        project = await db_manager.get_project(project_id)
        if not project:
            return f"Project {project_id} not found"

        tasks = await db_manager.get_project_tasks(project_id)
        completed = [t for t in tasks if t.get("status") == "completed"]

        prompt = f"""# {project.get('name')} Summary

Description: {project.get('description', 'N/A')}

## Task Overview
- Total: {len(tasks)}
- Completed: {len(completed)}
- Progress: {f"{(len(completed) / len(tasks) * 100):.0f}%" if len(tasks) > 0 else "N/A"}

## Tasks by Priority
"""
        for priority in ["high", "medium", "low"]:
            priority_tasks = [t for t in tasks if t.get("priority") == priority]
            prompt += f"- {priority.upper()}: {len(priority_tasks)}\n"

        return prompt
    except Exception as e:
        return f"Error generating project summary: {str(e)}"


@mcp.prompt()
async def overdue_analysis() -> str:
    """Prompt: Overdue tasks analysis workflow."""
    try:
        overdue = await db_manager.get_overdue_tasks()

        prompt = f"""# Overdue Tasks Analysis

Total overdue: {len(overdue)}

## Overdue Tasks by Priority
"""
        for priority in ["high", "medium", "low"]:
            priority_tasks = [t for t in overdue if t.get("priority") == priority]
            prompt += f"\n### {priority.upper()} Priority ({len(priority_tasks)})\n"
            for task in priority_tasks:
                prompt += f"- {task.get('title')} (due: {task.get('due_date')})\n"

        return prompt
    except Exception as e:
        return f"Error generating overdue analysis: {str(e)}"


# ==================== SERVER LIFECYCLE ====================


async def startup() -> None:
    """Initialize database on startup."""
    logger.info("Starting task tracker MCP server...")
    await db_manager.initialize()
    logger.info("Database initialized")


async def shutdown() -> None:
    """Close database on shutdown."""
    logger.info("Shutting down task tracker MCP server...")
    await db_manager.close()
    logger.info("Database closed")


async def main() -> None:
    """Run the MCP server."""
    try:
        await startup()

        # Run the server
        logger.info("Task tracker MCP server running")
        await mcp.run_stdio_async()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
