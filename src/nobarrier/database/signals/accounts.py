from sqlalchemy import event
from nobarrier.database.models.accounts import User


# BEFORE SAVE
@event.listens_for(User, "before_insert")
def user_pre_insert(mapper, connection, target: User):
    pass
    # target.username = target.username.lower()
    # if not target.language:
    #     target.language = "en"


# AFTER SAVE
@event.listens_for(User, "after_insert")
def user_post_insert(mapper, connection, target: User):
    pass
    # send_welcome_email(target.email)