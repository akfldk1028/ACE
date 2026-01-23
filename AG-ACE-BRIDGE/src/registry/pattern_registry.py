"""
Pattern Registry - Centralized Pattern Management

Manages registered patterns from AutoGen Studio and other sources.
Syncs pattern metadata to SharedMemory for cross-system visibility.

Features:
- Pattern registration and versioning
- SharedMemory synchronization
- Duplicate detection
- Auto-Claude notification

Usage:
    registry = PatternRegistry(shared_memory_url="http://localhost:8101")
    await registry.initialize()

    # Register new pattern
    pattern = await registry.register(pattern_event)

    # Get all patterns
    patterns = await registry.list_all()

    # Execute pattern
    result = await registry.execute(pattern_id)
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from src.watcher.pattern_watcher import PatternEvent, PatternEventType
from src.memory import SharedMemoryClient
from src.utils.logger import Loggers


class PatternStatus(str, Enum):
    """Pattern lifecycle status"""
    PENDING = "pending"        # Detected, not yet validated
    ACTIVE = "active"          # Validated and ready to execute
    SCHEDULED = "scheduled"    # Has active schedule
    DISABLED = "disabled"      # Manually disabled
    ERROR = "error"            # Validation or execution error


class PatternType(str, Enum):
    """Types of patterns"""
    WORKFLOW = "workflow"      # Multi-agent workflow
    AGENT = "agent"            # Single agent definition
    SKILL = "skill"            # Reusable skill
    TEMPLATE = "template"      # Base template


@dataclass
class RegisteredPattern:
    """A registered pattern in the system"""
    id: str
    name: str
    pattern_type: PatternType
    status: PatternStatus
    source_path: str
    checksum: str
    version: int
    data: Dict[str, Any]
    schedule: Optional[str] = None  # Cron expression
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    error_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pattern_type": self.pattern_type.value,
            "status": self.status.value,
            "source_path": self.source_path,
            "checksum": self.checksum,
            "version": self.version,
            "data": self.data,
            "schedule": self.schedule,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "execution_count": self.execution_count,
            "error_message": self.error_message,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegisteredPattern":
        return cls(
            id=data["id"],
            name=data["name"],
            pattern_type=PatternType(data["pattern_type"]),
            status=PatternStatus(data["status"]),
            source_path=data["source_path"],
            checksum=data["checksum"],
            version=data["version"],
            data=data["data"],
            schedule=data.get("schedule"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_executed_at=datetime.fromisoformat(data["last_executed_at"]) if data.get("last_executed_at") else None,
            execution_count=data.get("execution_count", 0),
            error_message=data.get("error_message"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


class PatternRegistry:
    """
    Central registry for all patterns.

    Manages pattern lifecycle:
    1. Detection (from PatternWatcher)
    2. Validation
    3. Registration
    4. Scheduling
    5. Execution tracking

    SharedMemory Keys:
    - patterns:{id} - Pattern data
    - patterns:index - List of all pattern IDs
    - patterns:by_name:{name} - Pattern ID by name
    """

    def __init__(
        self,
        shared_memory_url: str = "http://localhost:8101",
        enable_shared_memory: bool = True,
    ):
        self.shared_memory_url = shared_memory_url
        self.enable_shared_memory = enable_shared_memory
        self.logger = Loggers.registry()

        self._patterns: Dict[str, RegisteredPattern] = {}
        self._patterns_by_name: Dict[str, str] = {}  # name -> id
        self._patterns_by_checksum: Dict[str, str] = {}  # checksum -> id

        self._shared_memory: Optional[SharedMemoryClient] = None
        self._initialized = False

    async def initialize(self):
        """Initialize registry and load existing patterns"""
        if self._initialized:
            return

        # Initialize SharedMemory client
        if self.enable_shared_memory:
            self._shared_memory = SharedMemoryClient(
                base_url=self.shared_memory_url,
                source_name="pattern_registry",
            )

            # Load existing patterns from SharedMemory
            await self._load_from_shared_memory()

        self._initialized = True
        self.logger.info(
            "pattern_registry_initialized",
            pattern_count=len(self._patterns),
        )

    async def shutdown(self):
        """Shutdown registry"""
        if self._shared_memory:
            await self._shared_memory.close()
            self._shared_memory = None

        self._initialized = False
        self.logger.info("pattern_registry_shutdown")

    async def _load_from_shared_memory(self):
        """Load patterns from SharedMemory"""
        if not self._shared_memory:
            return

        try:
            # Get pattern index
            index_data = await self._shared_memory.get("patterns:index")
            if not index_data:
                return

            pattern_ids = index_data.get("pattern_ids", [])

            # Load each pattern
            for pattern_id in pattern_ids:
                pattern_data = await self._shared_memory.get(f"patterns:{pattern_id}")
                if pattern_data:
                    pattern = RegisteredPattern.from_dict(pattern_data)
                    self._patterns[pattern.id] = pattern
                    self._patterns_by_name[pattern.name] = pattern.id
                    self._patterns_by_checksum[pattern.checksum] = pattern.id

            self.logger.info(
                "loaded_patterns_from_shared_memory",
                count=len(self._patterns),
            )

        except Exception as e:
            self.logger.warning(
                "shared_memory_load_error",
                error=str(e),
            )

    async def _save_to_shared_memory(self, pattern: RegisteredPattern):
        """Save pattern to SharedMemory"""
        if not self._shared_memory:
            return

        try:
            # Save pattern data
            await self._shared_memory.store(
                key=f"patterns:{pattern.id}",
                data=pattern.to_dict(),
            )

            # Update index
            index_data = await self._shared_memory.get("patterns:index") or {}
            pattern_ids = set(index_data.get("pattern_ids", []))
            pattern_ids.add(pattern.id)

            await self._shared_memory.store(
                key="patterns:index",
                data={"pattern_ids": list(pattern_ids)},
            )

            # Update name lookup
            await self._shared_memory.store(
                key=f"patterns:by_name:{pattern.name}",
                data={"pattern_id": pattern.id},
            )

            # Publish event
            await self._shared_memory.publish_event(
                event_type="pattern_registered",
                data={
                    "pattern_id": pattern.id,
                    "pattern_name": pattern.name,
                    "status": pattern.status.value,
                },
            )

        except Exception as e:
            self.logger.warning(
                "shared_memory_save_error",
                pattern_id=pattern.id,
                error=str(e),
            )

    def _detect_pattern_type(self, data: Dict[str, Any]) -> PatternType:
        """Detect pattern type from data structure"""
        # AutoGen Studio workflow format
        if "nodes" in data or "edges" in data:
            return PatternType.WORKFLOW

        # AutoGen Studio agent format
        if "agent_type" in data or "model_config" in data:
            return PatternType.AGENT

        # Skill format
        if "skill_type" in data or "tools" in data:
            return PatternType.SKILL

        # Default to template
        return PatternType.TEMPLATE

    def _validate_pattern(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate pattern data structure.

        Returns:
            (is_valid, error_message)
        """
        if not data:
            return False, "Empty pattern data"

        # Must have name
        if "name" not in data:
            return False, "Pattern must have a name"

        # Check for basic structure based on type
        pattern_type = self._detect_pattern_type(data)

        if pattern_type == PatternType.WORKFLOW:
            # Workflows need nodes or steps
            if not data.get("nodes") and not data.get("steps"):
                return False, "Workflow must have nodes or steps"

        elif pattern_type == PatternType.AGENT:
            # Agents need type or config
            if not data.get("agent_type") and not data.get("config"):
                return False, "Agent must have agent_type or config"

        return True, None

    async def register(self, event: PatternEvent) -> Optional[RegisteredPattern]:
        """
        Register a pattern from a PatternEvent.

        Args:
            event: PatternEvent from PatternWatcher

        Returns:
            RegisteredPattern if successful, None if skipped/error
        """
        if not event.pattern_data:
            self.logger.warning(
                "register_no_data",
                file_path=event.file_path,
            )
            return None

        # Check for duplicate by checksum
        if event.checksum in self._patterns_by_checksum:
            existing_id = self._patterns_by_checksum[event.checksum]
            existing = self._patterns[existing_id]

            # If modified event, update timestamp
            if event.event_type == PatternEventType.MODIFIED:
                existing.updated_at = datetime.now()
                await self._save_to_shared_memory(existing)

            self.logger.info(
                "pattern_already_registered",
                pattern_id=existing_id,
                checksum=event.checksum,
            )
            return existing

        # Validate pattern
        is_valid, error_msg = self._validate_pattern(event.pattern_data)

        # Create pattern record
        pattern_id = str(uuid.uuid4())
        pattern_type = self._detect_pattern_type(event.pattern_data)

        # Check for existing pattern with same name (version update)
        version = 1
        if event.pattern_name in self._patterns_by_name:
            old_id = self._patterns_by_name[event.pattern_name]
            old_pattern = self._patterns[old_id]
            version = old_pattern.version + 1

            # Mark old pattern as disabled
            old_pattern.status = PatternStatus.DISABLED
            old_pattern.metadata["superseded_by"] = pattern_id

        pattern = RegisteredPattern(
            id=pattern_id,
            name=event.pattern_name,
            pattern_type=pattern_type,
            status=PatternStatus.ACTIVE if is_valid else PatternStatus.ERROR,
            source_path=event.file_path,
            checksum=event.checksum,
            version=version,
            data=event.pattern_data,
            error_message=error_msg,
            tags=event.pattern_data.get("tags", []),
            metadata={
                "source": "autogen_studio",
                "detected_at": event.timestamp.isoformat(),
            },
        )

        # Store in registry
        self._patterns[pattern.id] = pattern
        self._patterns_by_name[pattern.name] = pattern.id
        self._patterns_by_checksum[pattern.checksum] = pattern.id

        # Save to SharedMemory
        await self._save_to_shared_memory(pattern)

        self.logger.info(
            "pattern_registered",
            pattern_id=pattern.id,
            name=pattern.name,
            type=pattern.pattern_type.value,
            version=version,
            status=pattern.status.value,
        )

        return pattern

    async def unregister(self, pattern_id: str) -> bool:
        """Remove pattern from registry"""
        if pattern_id not in self._patterns:
            return False

        pattern = self._patterns[pattern_id]

        # Remove from lookups
        self._patterns_by_name.pop(pattern.name, None)
        self._patterns_by_checksum.pop(pattern.checksum, None)
        del self._patterns[pattern_id]

        # Update SharedMemory
        if self._shared_memory:
            try:
                # Update index
                index_data = await self._shared_memory.get("patterns:index") or {}
                pattern_ids = set(index_data.get("pattern_ids", []))
                pattern_ids.discard(pattern_id)

                await self._shared_memory.store(
                    key="patterns:index",
                    data={"pattern_ids": list(pattern_ids)},
                )

                # Publish event
                await self._shared_memory.publish_event(
                    event_type="pattern_unregistered",
                    data={"pattern_id": pattern_id, "pattern_name": pattern.name},
                )

            except Exception as e:
                self.logger.warning(
                    "shared_memory_unregister_error",
                    error=str(e),
                )

        self.logger.info("pattern_unregistered", pattern_id=pattern_id)
        return True

    async def update_status(
        self,
        pattern_id: str,
        status: PatternStatus,
        error_message: str = None,
    ) -> bool:
        """Update pattern status"""
        if pattern_id not in self._patterns:
            return False

        pattern = self._patterns[pattern_id]
        pattern.status = status
        pattern.updated_at = datetime.now()

        if error_message:
            pattern.error_message = error_message

        await self._save_to_shared_memory(pattern)
        return True

    async def set_schedule(
        self,
        pattern_id: str,
        cron_expression: str,
    ) -> bool:
        """Set execution schedule for pattern"""
        if pattern_id not in self._patterns:
            return False

        pattern = self._patterns[pattern_id]
        pattern.schedule = cron_expression
        pattern.status = PatternStatus.SCHEDULED
        pattern.updated_at = datetime.now()

        await self._save_to_shared_memory(pattern)

        self.logger.info(
            "pattern_scheduled",
            pattern_id=pattern_id,
            schedule=cron_expression,
        )
        return True

    async def record_execution(
        self,
        pattern_id: str,
        success: bool,
        error_message: str = None,
    ):
        """Record pattern execution"""
        if pattern_id not in self._patterns:
            return

        pattern = self._patterns[pattern_id]
        pattern.last_executed_at = datetime.now()
        pattern.execution_count += 1

        if not success and error_message:
            pattern.error_message = error_message

        await self._save_to_shared_memory(pattern)

        # Publish execution event
        if self._shared_memory:
            await self._shared_memory.publish_event(
                event_type="pattern_executed",
                data={
                    "pattern_id": pattern_id,
                    "pattern_name": pattern.name,
                    "success": success,
                    "execution_count": pattern.execution_count,
                },
            )

    def get(self, pattern_id: str) -> Optional[RegisteredPattern]:
        """Get pattern by ID"""
        return self._patterns.get(pattern_id)

    def get_by_name(self, name: str) -> Optional[RegisteredPattern]:
        """Get pattern by name"""
        pattern_id = self._patterns_by_name.get(name)
        if pattern_id:
            return self._patterns.get(pattern_id)
        return None

    def list_all(self) -> List[RegisteredPattern]:
        """Get all registered patterns"""
        return list(self._patterns.values())

    def list_active(self) -> List[RegisteredPattern]:
        """Get all active patterns"""
        return [
            p for p in self._patterns.values()
            if p.status in [PatternStatus.ACTIVE, PatternStatus.SCHEDULED]
        ]

    def list_scheduled(self) -> List[RegisteredPattern]:
        """Get all scheduled patterns"""
        return [
            p for p in self._patterns.values()
            if p.status == PatternStatus.SCHEDULED and p.schedule
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        patterns = list(self._patterns.values())

        return {
            "total": len(patterns),
            "by_status": {
                status.value: len([p for p in patterns if p.status == status])
                for status in PatternStatus
            },
            "by_type": {
                ptype.value: len([p for p in patterns if p.pattern_type == ptype])
                for ptype in PatternType
            },
            "total_executions": sum(p.execution_count for p in patterns),
        }
