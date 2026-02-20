from app import create_app
from app.extensions import db
from app.models import UserAccount, UserRole
from app.utils.security import hash_password

app = create_app()
with app.app_context():
    role = UserRole.query.filter_by(Name="admin").first()
    user = UserAccount(
        Username="admin",
        DisplayName="Admin",
        PasswordHash=hash_password("nMfcbKZR&5R6"),
        RoleId=role.Id,
    )
    db.session.add(user)
    db.session.commit()