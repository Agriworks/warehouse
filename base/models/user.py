from mongoengine import Document, StringField, IntField, EmailField

class User(Document):

    # Unique identifier for user
    user_id = IntField(required = True)

    # First name of user
    first_name = StringField(min_length=1, required=True)

    # Last name of user
    last_name = StringField(min_length=1, required=True)

    # Registered email address
    email = EmailField(required=True)

    ## TODO: make this more secure
    # Password
    password = StringField(min_length=1, required=True)

    ## TODO: abstract this out to separate model when we start on multiple orgs & user roles/permissions
    # What organisation the user is affliated with
    organization = StringField(required=False)

    # Indexing for name search
    def getFullname(self):
        return self.firstName + " " + self.lastName
    
    meta = {'indexes': [{'fields': ['$firstName', "$lastName"]}]}
