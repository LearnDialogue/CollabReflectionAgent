"""Initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_role = sa.Enum('STUDENT', 'ADMIN', name='userrole', create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)
    
    session_status = sa.Enum('ACTIVE', 'COMPLETED', name='sessionstatus', create_type=False)
    session_status.create(op.get_bind(), checkfirst=True)
    
    message_role = sa.Enum('user', 'assistant', name='messagerole', create_type=False)
    message_role.create(op.get_bind(), checkfirst=True)

    # Create students table
    op.create_table(
        'students',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='STUDENT'),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('pronouns', sa.String(50), nullable=True),
        sa.Column('tone_pref', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('student_id', sa.Uuid(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('status', session_status, nullable=False, server_default='ACTIVE'),
        sa.Column('current_stage', sa.String(50), nullable=False, server_default='RECALL_EVENT'),
        sa.Column('prompt_version', sa.String(20), nullable=False, server_default='v1'),
        sa.Column('model_name', sa.String(100), nullable=False, server_default='placeholder'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_sessions_student_id', 'sessions', ['student_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.Uuid(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('role', message_role, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('stage_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])

    # Create session_summaries table
    op.create_table(
        'session_summaries',
        sa.Column('session_id', sa.Uuid(as_uuid=True), sa.ForeignKey('sessions.id'), primary_key=True),
        sa.Column('event_summary', sa.Text(), nullable=True),
        sa.Column('challenges', sa.Text(), nullable=True),
        sa.Column('strategies', sa.Text(), nullable=True),
        sa.Column('next_goal', sa.Text(), nullable=True),
        sa.Column('share_plan_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create safety_incidents table
    op.create_table(
        'safety_incidents',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('student_id', sa.Uuid(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('session_id', sa.Uuid(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=True),
        sa.Column('message_id', sa.Uuid(as_uuid=True), sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('notified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_safety_incidents_student_id', 'safety_incidents', ['student_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('safety_incidents')
    op.drop_table('session_summaries')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('students')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS messagerole')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS userrole')
