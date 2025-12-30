# Import all the models here so that Base has them before being
# imported by Alembic
from app.db.database import Base  # noqa
from app.models.user import User  # noqa
from app.models.author import Author  # noqa
from app.models.book import Book  # noqa
from app.models.subscription import Subscription  # noqa
from app.models.settings import SystemSetting  # noqa
from app.models.usage import UsageLog  # noqa