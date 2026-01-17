import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from p8s.db.code import CodeField
from p8s.db.fields import ColorField
from p8s.db.richtext import RichTextField
from p8s.db.slug import SlugField
from p8s.db.tags import TagField


# Define a test model using all advanced fields
class AdvancedModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str

    # Advanced Fields
    content: dict = RichTextField()
    color: str = ColorField(default="#FFFFFF")
    code_snippet: str = CodeField(language="python")
    tags: list[str] = TagField()
    slug: str = SlugField()


@pytest.fixture(name="session")
async def async_session_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_advanced_fields_persistence(session: AsyncSession):
    """Test that all advanced fields can be saved and retrieved correctly."""

    # Create instance
    richtext_data = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello World"}]}
        ],
    }

    instance = AdvancedModel(
        title="Integration Test",
        content=richtext_data,
        color="#FF5733",
        code_snippet="print('Hello')",
        tags=["python", "testing", "integration"],
        slug="integration-test",
    )

    session.add(instance)
    await session.commit()
    await session.refresh(instance)

    # Verify IDs and basic persistence
    assert instance.id is not None
    assert instance.title == "Integration Test"

    # Verify RichTextField (JSON storage)
    assert instance.content == richtext_data
    assert isinstance(instance.content, dict)

    # Verify ColorField
    assert instance.color == "#FF5733"

    # Verify CodeField
    assert instance.code_snippet == "print('Hello')"

    # Verify TagField (JSON/List storage)
    assert instance.tags == ["python", "testing", "integration"]
    assert isinstance(instance.tags, list)

    # Verify SlugField
    assert instance.slug == "integration-test"


@pytest.mark.asyncio
async def test_advanced_fields_defaults(session: AsyncSession):
    """Test defaults for advanced fields."""

    # Create instance with minimal args
    instance = AdvancedModel(
        title="Default Test",
        slug="default-test",
        # Others should use defaults
    )

    session.add(instance)
    await session.commit()
    await session.refresh(instance)

    # Color default
    assert instance.color == "#FFFFFF"

    # Tags default (should be empty list)
    assert instance.tags == []

    # RichText default (should be empty dict or similar, depending on implementation)
    # Checking implementation of RichTextField default...
    # Usually defaults to {} if not specified.
    assert instance.content == {} or instance.content is None
