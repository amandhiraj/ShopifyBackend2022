from db import db


class ImageInv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text, nullable=False)
    pathImage = db.Column(db.Text, nullable=False)
    pathImageThumb= db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __init__(self, filename, pathImage, pathImageThumb, title, description):
        self.title = title
        self.description = description
        self.pathImage = pathImage
        self.pathImageThumb = pathImageThumb 
        self.filename = filename