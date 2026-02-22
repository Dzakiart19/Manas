import threading
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from app.core.config import settings
from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.models.supervisor import (
    ProcessInfo, 
    SupervisorActionResult, 
    SupervisorTimeout
)

logger = logging.getLogger(__name__)


class SupervisorService:
    def __init__(self):
        self.timeout_active = settings.SERVICE_TIMEOUT_MINUTES is not None
        self.shutdown_task = None
        self.shutdown_time = None
        self._auto_expand_enabled = True
        
        if settings.SERVICE_TIMEOUT_MINUTES is not None:
            self.shutdown_time = datetime.now() + timedelta(minutes=settings.SERVICE_TIMEOUT_MINUTES)

        logger.info("SupervisorService initialized (local mode, no Supervisord)")
    
    @property
    def auto_expand_enabled(self) -> bool:
        return self._auto_expand_enabled
    
    def disable_auto_expand(self):
        self._auto_expand_enabled = False
    
    def enable_auto_expand(self):
        self._auto_expand_enabled = True
    
    async def get_all_processes(self) -> List[ProcessInfo]:
        return [
            ProcessInfo(
                name="sandbox-api",
                group="sandbox",
                start=int(datetime.now().timestamp()),
                stop=0,
                now=int(datetime.now().timestamp()),
                state=20,
                statename="RUNNING",
                spawnerr="",
                exitstatus=0,
                logfile="",
                stdout_logfile="",
                stderr_logfile="",
                pid=1,
                description="pid 1, uptime 0:00:01"
            )
        ]
    
    async def stop_all_services(self) -> SupervisorActionResult:
        return SupervisorActionResult(status="stopped", result=[])
    
    async def shutdown(self) -> SupervisorActionResult:
        return SupervisorActionResult(status="shutdown", shutdown_result=True)
    
    async def restart_all_services(self) -> SupervisorActionResult:
        return SupervisorActionResult(
            status="restarted", 
            stop_result=[],
            start_result=[]
        )
    
    async def activate_timeout(self, minutes=None) -> SupervisorTimeout:
        timeout_minutes = minutes or settings.SERVICE_TIMEOUT_MINUTES
        
        if timeout_minutes is None:
            raise BadRequestException("Timeout not specified, and system default is no timeout")
            
        self.timeout_active = True
        self.shutdown_time = datetime.now() + timedelta(minutes=timeout_minutes)
        
        return SupervisorTimeout(
            status="timeout_activated",
            active=True,
            shutdown_time=self.shutdown_time.isoformat(),
            timeout_minutes=timeout_minutes
        )
    
    async def extend_timeout(self, minutes=None) -> SupervisorTimeout:
        timeout_minutes = minutes or settings.SERVICE_TIMEOUT_MINUTES
        
        if timeout_minutes is None:
            raise BadRequestException("Timeout not specified, and system default is no timeout")
            
        self.timeout_active = True
        self.shutdown_time = datetime.now() + timedelta(minutes=timeout_minutes)
        
        return SupervisorTimeout(
            status="timeout_extended",
            active=True,
            shutdown_time=self.shutdown_time.isoformat(),
            timeout_minutes=timeout_minutes
        )
    
    async def cancel_timeout(self) -> SupervisorTimeout:
        if not self.timeout_active:
            return SupervisorTimeout(status="no_timeout_active", active=False)
        
        self.timeout_active = False
        self.shutdown_time = None
        self._auto_expand_enabled = True
        
        return SupervisorTimeout(status="timeout_cancelled", active=False)
    
    async def get_timeout_status(self) -> SupervisorTimeout:
        if not self.timeout_active:
            return SupervisorTimeout(active=False)
        
        remaining_seconds = 0
        if self.shutdown_time:
            remaining = self.shutdown_time - datetime.now()
            remaining_seconds = max(0, remaining.total_seconds())
        
        return SupervisorTimeout(
            active=self.timeout_active,
            shutdown_time=self.shutdown_time.isoformat() if self.shutdown_time else None,
            remaining_seconds=remaining_seconds
        )


supervisor_service = SupervisorService()
