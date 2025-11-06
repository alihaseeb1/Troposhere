from sqlalchemy import Enum
from ..models import Logging
from sqlalchemy.orm import Session
from datetime import datetime


def log_operation(
    db: Session,
    *,
    tablename: str,
    operation: str,
    who_id: int,
    new_val: dict | None = None,
    old_val: dict | None = None,
):
    """Logs all CRUD operation to the logging table."""

    old_val=safe_log(old_val) if old_val else None
    new_val=safe_log(new_val) if new_val else None

    if old_val:
        if "_sa_instance_state" in old_val:
            del old_val["_sa_instance_state"]
    if new_val:
        if "_sa_instance_state" in new_val:
            del new_val["_sa_instance_state"]

    log_entry = Logging(
        tablename=tablename,
        operation=operation.upper(),
        who=who_id,
        old_val=old_val,
        new_val=new_val,
    )
    db.add(log_entry)
    db.commit()

import json
from datetime import datetime
from enum import Enum

def safe_log(details, _depth=0, _max_depth=2):
    if details is None:
        return None

    # Stop recursion at depth limit
    if _depth > _max_depth:
        return str(details)

    if isinstance(details, dict):
        return {k: safe_log(v, _depth + 1, _max_depth) for k, v in details.items()}

    if isinstance(details, list):
        return [safe_log(v, _depth + 1, _max_depth) for v in details]

    if isinstance(details, Enum):
        return details.value

    if isinstance(details, datetime):
        return details.isoformat()

    if str(details).startswith("<sqlalchemy.orm.state.InstanceState"):
        return None

    if hasattr(details, "__dict__"):
        return {
            k: safe_log(v, _depth + 1, _max_depth)
            for k, v in details.__dict__.items()
            if not k.startswith("_sa_")
        }

    return details