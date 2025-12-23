"""Database management for task manager MCP server."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for task management system."""

    def __init__(self, db_path: str = "tasks.db"):
        """Initialize database manager with given path."""
        self.db_path = Path(db_path)
        self.connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        try:
            self.connection = await aiosqlite.connect(str(self.db_path))
            self.connection.row_factory = aiosqlite.Row
            await self._create_schema()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def close(self) -> None:
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def _create_schema(self) -> None:
        """Create database schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            return

        with open(schema_path) as f:
            schema = f.read()

        await self.connection.executescript(schema)
        await self.connection.commit()
        logger.info("Database schema created/verified")

    @asynccontextmanager
    async def _get_connection(self):
        """Context manager for database operations."""
        if not self.connection:
            await self.initialize()
        yield self.connection

    # ==================== PROJECT OPERATIONS ====================

    async def create_project(self, name: str, description: str = "") -> dict:
        """Create a new project."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "INSERT INTO projects (name, description) VALUES (?, ?)",
                    (name, description),
                )
                await conn.commit()
                project_id = cursor.lastrowid

                # Fetch and return the created project
                cursor = await conn.execute(
                    "SELECT * FROM projects WHERE id = ?", (project_id,)
                )
                row = await cursor.fetchone()
                return self._row_to_dict(row)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise

    async def get_project(self, project_id: int) -> Optional[dict]:
        """Get project by ID."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM projects WHERE id = ?", (project_id,)
                )
                row = await cursor.fetchone()
                return self._row_to_dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None

    async def list_projects(self) -> list[dict]:
        """List all projects."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM projects ORDER BY name"
                )
                rows = await cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    async def update_project(self, project_id: int, **kwargs) -> Optional[dict]:
        """Update project fields."""
        try:
            allowed_fields = {"name", "description"}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_fields:
                return await self.get_project(project_id)

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [project_id]

            async with self._get_connection() as conn:
                await conn.execute(
                    f"UPDATE projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    values,
                )
                await conn.commit()

            return await self.get_project(project_id)
        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            return None

    async def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        try:
            async with self._get_connection() as conn:
                await conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return False

    # ==================== TASK OPERATIONS ====================

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        status: str = "pending",
        project_id: Optional[int] = None,
        due_date: Optional[str] = None,
    ) -> dict:
        """Create a new task."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """INSERT INTO tasks
                    (title, description, priority, status, project_id, due_date)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (title, description, priority, status, project_id, due_date),
                )
                await conn.commit()
                task_id = cursor.lastrowid

                return await self.get_task(task_id)
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    async def get_task(self, task_id: int) -> Optional[dict]:
        """Get task by ID with tags."""
        try:
            async with self._get_connection() as conn:
                # Get task
                cursor = await conn.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                )
                row = await cursor.fetchone()
                if not row:
                    return None

                task = self._row_to_dict(row)

                # Get tags
                cursor = await conn.execute(
                    """SELECT t.id, t.name FROM tags t
                    JOIN task_tags tt ON t.id = tt.tag_id
                    WHERE tt.task_id = ?""",
                    (task_id,),
                )
                tags = [dict(tag) for tag in await cursor.fetchall()]
                task["tags"] = tags

                return task
        except Exception as e:
            logger.error(f"Failed to get task: {e}")
            return None

    async def list_tasks(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all tasks with pagination."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM tasks
                    ORDER BY priority = 'high' DESC, due_date ASC
                    LIMIT ? OFFSET ?""",
                    (limit, offset),
                )
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = self._row_to_dict(row)
                    # Get tags for each task
                    tags_cursor = await conn.execute(
                        """SELECT t.id, t.name FROM tags t
                        JOIN task_tags tt ON t.id = tt.tag_id
                        WHERE tt.task_id = ?""",
                        (task["id"],),
                    )
                    tags = [dict(tag) for tag in await tags_cursor.fetchall()]
                    task["tags"] = tags
                    tasks.append(task)
                return tasks
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

    async def update_task(self, task_id: int, **kwargs) -> Optional[dict]:
        """Update task fields."""
        try:
            allowed_fields = {"title", "description", "status", "priority", "due_date"}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_fields:
                return await self.get_task(task_id)

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [task_id]

            async with self._get_connection() as conn:
                await conn.execute(
                    f"UPDATE tasks SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    values,
                )
                await conn.commit()

            return await self.get_task(task_id)
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return None

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        try:
            async with self._get_connection() as conn:
                await conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return False

    # ==================== TAG OPERATIONS ====================

    async def add_tag(self, task_id: int, tag_name: str) -> bool:
        """Add a tag to a task."""
        try:
            async with self._get_connection() as conn:
                # Get or create tag
                cursor = await conn.execute(
                    "SELECT id FROM tags WHERE name = ?", (tag_name,)
                )
                tag = await cursor.fetchone()

                if not tag:
                    cursor = await conn.execute(
                        "INSERT INTO tags (name) VALUES (?)", (tag_name,)
                    )
                    await conn.commit()
                    tag_id = cursor.lastrowid
                else:
                    tag_id = tag["id"]

                # Add to task
                await conn.execute(
                    "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tag_id),
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add tag: {e}")
            return False

    async def remove_tag(self, task_id: int, tag_name: str) -> bool:
        """Remove a tag from a task."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT id FROM tags WHERE name = ?", (tag_name,)
                )
                tag = await cursor.fetchone()

                if not tag:
                    return False

                await conn.execute(
                    "DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?",
                    (task_id, tag["id"]),
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to remove tag: {e}")
            return False

    async def list_tags(self) -> list[dict]:
        """List all tags."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM tags ORDER BY name")
                rows = await cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list tags: {e}")
            return []

    # ==================== SEARCH OPERATIONS ====================

    async def search_tasks(self, query: str) -> list[dict]:
        """Search tasks using full-text search."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT t.* FROM tasks t
                    JOIN tasks_fts f ON t.id = f.rowid
                    WHERE tasks_fts MATCH ?
                    ORDER BY rank""",
                    (query,),
                )
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = self._row_to_dict(row)
                    tags_cursor = await conn.execute(
                        """SELECT t.id, t.name FROM tags t
                        JOIN task_tags tt ON t.id = tt.tag_id
                        WHERE tt.task_id = ?""",
                        (task["id"],),
                    )
                    tags = [dict(tag) for tag in await tags_cursor.fetchall()]
                    task["tags"] = tags
                    tasks.append(task)
                return tasks
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []

    async def filter_tasks(self, **filters) -> list[dict]:
        """Filter tasks by various criteria."""
        try:
            async with self._get_connection() as conn:
                query = "SELECT * FROM tasks WHERE 1=1"
                params = []

                if "status" in filters:
                    query += " AND status = ?"
                    params.append(filters["status"])

                if "priority" in filters:
                    query += " AND priority = ?"
                    params.append(filters["priority"])

                if "project_id" in filters:
                    query += " AND project_id = ?"
                    params.append(filters["project_id"])

                if "tag_name" in filters:
                    query = f"""SELECT DISTINCT t.* FROM tasks t
                    JOIN task_tags tt ON t.id = tt.task_id
                    JOIN tags tg ON tt.tag_id = tg.id
                    WHERE tg.name = ? AND {' AND '.join([k + ' = ?' for k in [k for k in filters.keys() if k != 'tag_name']])}"""
                    params = [filters["tag_name"]] + [
                        v
                        for k, v in filters.items()
                        if k != "tag_name" and k in ["status", "priority", "project_id"]
                    ]

                query += " ORDER BY priority = 'high' DESC, due_date ASC"

                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = self._row_to_dict(row)
                    tags_cursor = await conn.execute(
                        """SELECT t.id, t.name FROM tags t
                        JOIN task_tags tt ON t.id = tt.tag_id
                        WHERE tt.task_id = ?""",
                        (task["id"],),
                    )
                    tags = [dict(tag) for tag in await tags_cursor.fetchall()]
                    task["tags"] = tags
                    tasks.append(task)
                return tasks
        except Exception as e:
            logger.error(f"Failed to filter tasks: {e}")
            return []

    # ==================== ANALYTICS OPERATIONS ====================

    async def get_task_statistics(self) -> dict:
        """Get task statistics."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) as total FROM tasks")
                total = (await cursor.fetchone())["total"]

                cursor = await conn.execute(
                    "SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'"
                )
                completed = (await cursor.fetchone())["completed"]

                cursor = await conn.execute(
                    "SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'"
                )
                pending = (await cursor.fetchone())["pending"]

                cursor = await conn.execute(
                    "SELECT COUNT(*) as high_priority FROM tasks WHERE priority = 'high'"
                )
                high_priority = (await cursor.fetchone())["high_priority"]

                return {
                    "total": total,
                    "completed": completed,
                    "pending": pending,
                    "in_progress": total - completed - pending,
                    "high_priority": high_priority,
                    "completion_rate": (completed / total * 100) if total > 0 else 0,
                }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    async def get_overdue_tasks(self) -> list[dict]:
        """Get overdue tasks."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM tasks
                    WHERE due_date < date('now') AND status != 'completed'
                    ORDER BY due_date ASC"""
                )
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = self._row_to_dict(row)
                    tags_cursor = await conn.execute(
                        """SELECT t.id, t.name FROM tags t
                        JOIN task_tags tt ON t.id = tt.tag_id
                        WHERE tt.task_id = ?""",
                        (task["id"],),
                    )
                    tags = [dict(tag) for tag in await tags_cursor.fetchall()]
                    task["tags"] = tags
                    tasks.append(task)
                return tasks
        except Exception as e:
            logger.error(f"Failed to get overdue tasks: {e}")
            return []

    async def get_project_tasks(self, project_id: int) -> list[dict]:
        """Get all tasks for a project."""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    """SELECT * FROM tasks WHERE project_id = ?
                    ORDER BY priority = 'high' DESC, due_date ASC""",
                    (project_id,),
                )
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = self._row_to_dict(row)
                    tags_cursor = await conn.execute(
                        """SELECT t.id, t.name FROM tags t
                        JOIN task_tags tt ON t.id = tt.tag_id
                        WHERE tt.task_id = ?""",
                        (task["id"],),
                    )
                    tags = [dict(tag) for tag in await tags_cursor.fetchall()]
                    task["tags"] = tags
                    tasks.append(task)
                return tasks
        except Exception as e:
            logger.error(f"Failed to get project tasks: {e}")
            return []

    # ==================== UTILITY METHODS ====================

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert aiosqlite.Row to dictionary."""
        if row is None:
            return {}
        return dict(row)
