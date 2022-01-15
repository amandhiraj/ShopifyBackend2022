#app.py
from flask import Flask, flash, request, redirect, url_for, render_template
import os
from werkzeug.utils import secure_filename
from PIL import Image as Thumb
from models import ImageInv
from db import db_init, db
import uuid 

app = Flask(__name__)
 
UPLOAD_FOLDER = 'static/uploads/'
UPLOAD_FOLDER_THUMBNAIL = 'static/uploads/thumbnails'

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_THUMBNAIL'] = UPLOAD_FOLDER_THUMBNAIL
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#init the database
db_init(app)

#restrict images types
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
     

#mainpage
@app.route('/')
def home():
    return render_template('upload.html')

#new entry page/home
@app.route('/', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        #ignore request if no files attached
        if 'file' not in request.files:
            flash('No image uploaded')
            return redirect(request.url)
        
        #grab the file data
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        
        #check for fiel type and if file uploaded
        if file and allowed_file(file.filename):

            #using uuid make the image unique which can be used to pull data from the database
            filename = secure_filename(str(uuid.uuid1()) + "" + (file.filename))

            #check for if the inputs of title and description is given
            if not request.form['title'] or not request.form['description']:
                flash('please enter all the fields', 'error')
            else:
                #save original copy
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                #save thumbnail using the pillow lib
                thumbImg = Thumb.open(f'static/uploads/{filename}')
                MAX_SIZE = (100, 100)
                thumbImg.thumbnail(MAX_SIZE)
        
                # creating thumbnail to show on the website rather the full image itself
                thumbImg.save(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename))
                
                flash('Image successfully uploaded')

                #Save the data of the image to the database
                pathToImage = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pathToImageThumb = os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename)
                imgData = ImageInv(filename=filename, pathImage=pathToImage, pathImageThumb=pathToImageThumb, title=request.form['title'], description=request.form['description'])
                db.session.add(imgData)
                db.session.commit() 

            return redirect('/display')
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)
 
 #displays the inventory of exisitng items
@app.route('/display')
def display_image():
    #grab the query of the inventory
    ImgDataQuery = ImageInv.query.all()
    return render_template('inventory.html', data = ImgDataQuery)

#delete's the image given the filename which is unique parameter
@app.route('/delete/<string:filename>', methods=['POST', 'GET'])
def deleteImg(filename):

    #used the thumbnail path to delete the database entry's and both (thumbnail and image) local images store on the machine.
    pathToCheck = os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename)
    imagePath = ImageInv.query.filter_by(pathImageThumb=pathToCheck).first()
    if request.method == 'GET':
        if imagePath: 
            #remove thumbnail
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename))
            #remove image
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #make changes on the database
            db.session.delete(imagePath)
            db.session.commit()
            return redirect("/display")
    return redirect("/display")

#updates the entry using the filename as the unique param.
@app.route('/update/<string:filenameToUpdate>', methods=['POST', 'GET'])
def editImg(filenameToUpdate):
    if request.method == 'GET':
        return render_template("update.html")
    if request.method == 'POST':
        #gets the exisiting data of the file to edit
        fileData = ImageInv.query.filter_by(filename=filenameToUpdate)
        #receive the new image
        file = request.files['file']

        #check if the new image is uploaded and checks if exisitng image data is exists
        if fileData and file and allowed_file(file.filename):
            #create unique filename
            filename = secure_filename(str(uuid.uuid1()) + "" + (file.filename))
            #check for vaild inputs
            if not request.form['title'] or not request.form['description']:
                flash('please enter all the fields', 'error')
            else:
                #save new copy and delete previous file
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #delete prev data of the entry
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filenameToUpdate)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filenameToUpdate))

                #save new thumbnail and delete previous file
                thumbImg = Thumb.open(f'static/uploads/{filename}')
                MAX_SIZE = (100, 100)
                thumbImg.thumbnail(MAX_SIZE)
                thumbImg.save(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename))

                #delete prev data of the entry
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filenameToUpdate)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filenameToUpdate))

                #update the database with new data
                fileData.update(dict(
                    filename=filename,
                    title=request.form['title'],
                    description=request.form['description'],
                    pathImage=os.path.join(app.config['UPLOAD_FOLDER'], filename),
                    pathImageThumb=os.path.join(app.config['UPLOAD_FOLDER_THUMBNAIL'], filename)
                ))
                db.session.commit() 
            return redirect("/display")
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)
    return redirect("/display")
 
if __name__ == "__main__":
    app.run(port=5000)