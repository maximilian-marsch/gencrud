from applic.database import db
from sqlalchemy.orm import relationship

class Role( db.Model ):
    """Model for the role table, this is generated by the gencrud.py module
    When modifing the file make sure that you remove the table from the configuration.
    """
    __tablename__       = 'WA_ROLES'
    D_ROLE_ID = db.Column( Integer, autoincrement = True, primary_key = True)
    D_ROLE = db.Column( String( 20 ))
    USERS = relationship( "RELATION"User)

