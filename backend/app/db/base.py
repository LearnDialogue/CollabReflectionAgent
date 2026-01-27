"""
SQLAlchemy base class.
"""

from sqlalchemy.orm import declarative_base

# Create base class for models
Base = declarative_base()

__all__ = ["Base"]
