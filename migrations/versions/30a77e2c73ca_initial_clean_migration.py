"""Initial clean migration

Revision ID: 30a77e2c73ca
Revises: 
Create Date: 2025-06-13 10:00:42.172732

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30a77e2c73ca'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('committees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('forums',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('university_domain', sa.String(length=120), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('university_domain')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=True),
    sa.Column('student_number', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('job_title', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('university', sa.String(length=100), nullable=True),
    sa.Column('faculty', sa.String(length=100), nullable=True),
    sa.Column('major', sa.String(length=100), nullable=True),
    sa.Column('quote', sa.Text(), nullable=True),
    sa.Column('skills', sa.Text(), nullable=True),
    sa.Column('profile_picture', sa.String(length=255), nullable=True),
    sa.Column('cover_picture', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('committee_id', sa.Integer(), nullable=True),
    sa.Column('forum_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], name='fk_posts_committee_id', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['forum_id'], ['forums.id'], name='fk_posts_forum_id', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_posts_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_committees',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('committee_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], name='fk_usercommittees_committee_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_usercommittees_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'committee_id')
    )
    op.create_table('user_followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], name='fk_comments_parent_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], name='fk_comments_post_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_comments_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('post_likes',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'post_id')
    )
    op.create_table('comment_votes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('comment_id', sa.Integer(), nullable=False),
    sa.Column('vote', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_vote')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comment_votes')
    op.drop_table('post_likes')
    op.drop_table('comments')
    op.drop_table('user_followers')
    op.drop_table('user_committees')
    op.drop_table('posts')
    op.drop_table('users')
    op.drop_table('forums')
    op.drop_table('committees')
    # ### end Alembic commands ###
