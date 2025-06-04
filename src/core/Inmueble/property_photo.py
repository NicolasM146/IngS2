from src.core.database import db
import os
from werkzeug.utils import secure_filename

class PropertyPhoto(db.Model):
    __tablename__ = 'property_photos'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    
    property = db.relationship("Property", back_populates="photos")

    @classmethod
    def get_upload_folder(cls):
        return os.path.join('static', 'uploads', 'properties')

    @classmethod
    def allowed_file(cls, filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS