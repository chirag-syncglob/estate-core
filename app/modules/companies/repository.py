from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseException
from app.db.models.companies import Company


class CompanyRepository:
    def __init__(self, db):
        self.db = db
        
    def list_companies(self):
        try:
            return self.db.query(Company).order_by(Company.name.asc()).all()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to load companies right now.") from exc
        
        
    def create_company(self, name: str, admin_id: str):
        try:
            company = Company(name=name, admin_id=admin_id)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            return company
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseException(message="Unable to create company right now.") from exc