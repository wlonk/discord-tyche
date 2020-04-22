from tortoise import fields, Tortoise
from tortoise.models import Model


async def init():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['tyche.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()


class EmojiMessage(Model):
    id = fields.IntField(pk=True)
    message_id = fields.IntField()
    emoji = fields.TextField()
    role = fields.TextField()
