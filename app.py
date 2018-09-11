from flask import Flask
from flask import render_template, redirect, url_for
from flask import request
from flask import jsonify

from werkzeug.utils import secure_filename
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread

from bar import Bar

UPLOAD_FOLDER = os.path.dirname(__file__) + '/static/pictures/temp/'
PICTURE_FOLDER = os.path.dirname(__file__) + '/static/pictures/'
rel_folder = 'pictures/temp/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

print(PICTURE_FOLDER)
print(__name__)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

'''BARTENDER2 SECTION'''
'''
bar = Bar()
bar.create_pump(11)
bar.create_pump(14, flowrate=1000)
bar.create_pump(17)
bar.create_pump(23)
bar.create_pump(25)

bar.create_ingredient(name="Wodka", percentage=45, bottlesize=700)
bar.ingredients[0].assignPump(bar.pumps[0])

bar.create_ingredient(name="Ginger Beer", percentage=0, bottlesize=500)
bar.ingredients[1].assignPump(bar.pumps[1])

bar.create_ingredient(name="Gin", percentage=45, bottlesize=700)
bar.ingredients[2].assignPump(bar.pumps[3])

bar.create_ingredient(name='Red Bull', percentage=0, bottlesize=200)
bar.ingredients[3].assignPump(bar.pumps[2])

bar.create_ingredient(name='Tonic Water', percentage=0, bottlesize=500)
bar.ingredients[4].assignPump(bar.pumps[4])

bar.create_drink(name="Moscow Mule", type='Longdrink', picture='moscowMule.png', description="This is a drink from Moscow.")
bar.drinks[0].create_version(shortname='single', ingredients=[bar.ingredients[0], bar.ingredients[1]], proportions=[40,60], glassize=200)
bar.drinks[0].create_version(shortname='double', ingredients=[bar.ingredients[0], bar.ingredients[1]], proportions=[50,50], glassize=200)
bar.drinks[0].create_version(shortname='big', ingredients=[bar.ingredients[0], bar.ingredients[1]], proportions=[60,40], glassize=8000)

bar.create_drink(name='Wodka Bull', type='Longdrink', picture='wodkaEnergy.png', description='This is a drink from Austria.')
bar.drinks[1].create_version(shortname='single', ingredients=[bar.ingredients[0], bar.ingredients[3]], proportions=[30,70], glassize=200)

bar.create_drink(name='Gin Tonic', type='Longdrink', picture='ginTonic.png', description='This is a fancy hyped drink.')
bar.drinks[2].create_version(shortname='single', ingredients=[bar.ingredients[2], bar.ingredients[4]], proportions=[30,70], glassize=200)



bar.create_pump(27)
bar.create_pump(32)

bar.create_ingredient(name="Liqueur 43", percentage=31, bottlesize=700)
bar.ingredients[5].assignPump(bar.pumps[5])

bar.create_ingredient(name="Milch", percentage=0, bottlesize=1000)
bar.ingredients[6].assignPump(bar.pumps[6])

bar.create_drink(name="Milch 43", type='Longdrink', picture='milch43.png', description="This is Vreni's and Felix' drink ❤️.")

bar.drinks[3].create_version(shortname='single', ingredients=[bar.ingredients[5], bar.ingredients[6]], proportions=[30,70], glassize=200)

bar.save_config('config')
'''

'''BARTENDER2 SECTION END'''

# bar = reload_config('config')
bar = Bar(folder='config')

@app.route("/")
def startpage():
    bar.save_config('config')
    return render_template('index.html', drinks=bar.drinks)

@app.route("/detail", methods=['GET'])
def detailview():
    iddrink = int(request.args.get('iddrink'))
    print(iddrink)
    drink = bar.drinks[iddrink]

    return render_template('detail.html', drink=drink, iddrink=iddrink)

@app.route("/make", methods=['POST'])
def makeview():
    iddrink = int(request.form.get('iddrink'))
    idversion = int(request.form.get('idversion'))
    duration = bar.drinks[iddrink].versions[idversion].duration
    bar.drinks[iddrink].versions[idversion].make()
    bar.save_config('config')
    return jsonify({'text': duration})

@app.route("/ingredients", methods=['GET','POST'])
def ingredientsview():
    if request.form.get('toast'):
        toast = request.form.get('toast')
    else:
        toast = ''
    return render_template('/ingredients.html', ingredients=bar.ingredients, pumps=bar.pumps, bar=bar, toast=toast)

@app.route("/ingredients/changeBottleForm", methods=['POST'])
def changeBottleFormSnippet():
    idingredient = int(request.form.get('idingredient'))
    return render_template('snippets/changeBottleForm.html', idingredient=idingredient, ingredient=bar.ingredients[idingredient], pumps=bar.pumps, bar=bar)

@app.route("/submit/newIngredient", methods=['POST'])
def submitNewIngredient():
    name = request.form.get('name')
    pump = request.form.get('pump')
    percentage = int(request.form.get('percentage'))
    bottlesize = int(float(request.form.get('bottlesize')) * 1000)

    if pump == "":
        pumpid = None
    else:
        pumpid = int(pump)
    bar.create_ingredient(name=name, percentage=percentage, bottlesize=bottlesize, pump=pumpid)
    bar.save_config('config')
    return jsonify({'error': 0})

@app.route("/submit/changeIngredient", methods=['POST'])
def submitChangeIngredient():
    idingredient = int(request.form.get('idingredient'))
    name = request.form.get('name')
    pumpid = request.form.get('pump')
    percentage = int(request.form.get('percentage'))
    bottlesize = int(float(request.form.get('bottlesize')) * 1000)

    print(str(idingredient)+ " " + name + " " + pumpid + " " + str(percentage) + " " + str(bottlesize))

    if pumpid == "":
        pump = None
    else:
        pump = bar.pumps[int(pumpid)]

    bar.ingredients[idingredient].change_Ingredient(name=name, pump=pump, percentage=percentage, bottlesize=bottlesize)
    bar.save_config('config')
    return jsonify({'error': 0})

@app.route("/submit/deleteIngredient", methods=['POST'])
def submitDeleteIngredient():

    idingredient = int(request.form.get('idingredient'))
    bar.delete_ingredient(ingredient=bar.ingredients[idingredient])
    bar.save_config('config')
    return jsonify({'error': 0})

@app.route("/pumps", methods=['GET','POST'])
def pumpsview():
    if request.form.get('toast'):
        toast = request.form.get('toast')
    else:
        toast = ''
    return render_template('/pumps.html', pumps=bar.pumps, bar=bar, toast=toast)

@app.route("/pumps/changePumpForm", methods=['POST'])
def changePumpFormSnippet():
    idpump = int(request.form.get('idpump'))
    return render_template('snippets/changePumpForm.html', idpump=idpump, pump=bar.pumps[idpump], bar=bar)

@app.route("/submit/newPump", methods=['POST'])
def submitNewPump():
    pin = int(request.form.get('pin'))
    flowrate = request.form.get('flowrate')

    if flowrate == "":
        bar.create_pump(pin=pin)
    else:
        bar.create_pump(pin=pin, flowrate=int(flowrate))
    bar.save_config('config')
    return jsonify({'error': 0})

@app.route("/submit/changePump", methods=['POST'])
def submitChangePump():
    try:
        pin = int(request.form.get('pin'))
        flowrate = request.form.get('flowrate')
        idpump = int(request.form.get('idpump'))

        if not flowrate == "":
            bar.pumps[idpump].flowrate = int(flowrate)
        bar.pumps[idpump].pin = pin
        bar.save_config('config')
        return jsonify({'error': 0})
    except:
        return jsonify({'error': 1})

@app.route("/submit/deletePump", methods=['POST'])
def submitDeletePump():
    idpump = int(request.form.get('idpump'))
    bar.delete_pump(bar.pumps[idpump])
    bar.save_config('config')
    return jsonify({'error': 0})



@app.route("/drinks", methods=['GET', 'POST'])
def drinks(toast=''):
    if request.form.get('toast'):
        toast = request.form.get('toast')
    elif toast != '':
        toast = toast
    else:
        toast = ''
    filelist = os.listdir(PICTURE_FOLDER)
    for fichier in filelist[:]:  # filelist[:] makes a copy of filelist.
        if not (fichier.endswith(".png")):
            filelist.remove(fichier)
    print(filelist)
    return render_template('/drinks/drinks.html', toast=toast, pictures=filelist, drinks=bar.drinks)

@app.route("/drinks/chooseImage")
def cropperChooseImage():
    return render_template('drinks/chooseImage.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/drinks/cropImage", methods=['POST'])
def cropperCropImage():
    if request.method == 'POST':
        if request.form.get('path'):
            print(request.form.get('path'))
            return render_template('drinks/cropImage.html', path=request.form.get('path'))
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return render_template('drinks/drinks.html')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('No selected file')
            return render_template('drinks/drinks.html')
        if file and allowed_file(file.filename):
            print("works")
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('drinks/drinks.html', path=rel_folder+filename)

    return render_template('drinks/drinks.html')
@app.route("/submit/newDrink", methods=['POST'])
def submitNewDrink():
    try:
        name = request.form.get('name')
        type = request.form.get('type')
        desc = request.form.get('desc')
        pic = request.form.get('picture')

        if name == '' or type == '' or pic == '':
            raise Exception()

        print(name + " " + type + " " + desc + " " + pic)

        bar.create_drink(name=name, type=type, picture=pic, description=desc)
        bar.save_config('config')
        return drinks('Successfully added new drink!')
    except:
        return drinks('Something went wrong..')

@app.route("/submit/deleteDrink", methods=['POST'])
def submitDeleteDrink():
    try:
        iddrink = request.form.get('iddrink')

        if iddrink == "":
            raise Exception()
        iddrink = int(iddrink)

        bar.delete_drink(drink=bar.drinks[iddrink])
        bar.save_config('config')
        return drinks('Successfully delete drink!')
    except:
        return drinks('Something went wrong..')

@app.route("/drinks/changeDrinkForm", methods=['POST'])
def changeDrinkFormSnippet():
    iddrink = int(request.form.get('iddrink'))

    filelist = os.listdir(PICTURE_FOLDER)
    for fichier in filelist[:]:  # filelist[:] makes a copy of filelist.
        if not (fichier.endswith(".png")):
            filelist.remove(fichier)

    return render_template('drinks/changeDrinkForm.html', iddrink=iddrink, drink=bar.drinks[iddrink], pictures=filelist, bar=bar)

@app.route("/submit/newVersion", methods=['POST'])
def submitNewVersion():
    try:
        iddrink = request.form.get('iddrink')
        shortname = request.form.get('shortname')
        size = request.form.get('size')
        ings = request.form.getlist('ing[]')
        props = request.form.getlist('prop[]')

        if iddrink == "" or shortname == "" or size == "" or len(ings) == 0 or len(props) == 0:
            return drinks('You have to fillout all fields.')

        iddrink = int(iddrink)
        size = int(size)

        ingredients = []
        proportions = []
        for ing, prop in zip(ings, props):
            ingredients.append(bar.ingredients[int(ing)])
            proportions.append(int(prop))

        print(proportions)
        print(ingredients)

        bar.drinks[iddrink].create_version(shortname=shortname, ingredients=ingredients, proportions=proportions, glassize=size)
        bar.save_config('config')
        return drinks('Successfully added new drink!')
    except:
        return drinks('Something went wrong..')

@app.route("/submit/deleteVersion", methods=['POST'])
def submitDeleteVersion():
    try:
        iddrink = request.form.get('iddrink')
        idversion = request.form.get('idversion')

        if iddrink == "" or idversion == "":
            raise Exception()
        iddrink = int(iddrink)
        idversion = int(idversion)

        print(iddrink)
        print(idversion)

        bar.drinks[iddrink].delete_version(versionid=idversion)
        bar.save_config('config')
        return drinks('Successfully delete version!')
    except:
        return drinks('Something went wrong..')

@app.route("/swapping")
def swapView(toast=""):
    if request.method == 'GET':
        toast = request.args.get('toast')
    return render_template('/swapping.html', toast=toast, ingredients=bar.ingredients)

@app.route("/tools/swap", methods=['GET','POST'])
def swapAction():
    try:
        iding = "";
        if request.method == 'POST':
            iding = request.form.get('iding')
        else:
            iding = request.args.get('iding')

        if iding == "":
            raise Exception()

        iding = int(iding)

        bar.ingredients[iding].swapBottle()
        bar.save_config('config')
        return redirect(url_for('swapView', toast='Bottle refilled.'))
        return swapView('Bottle refilled.')
    except:
        return swapView('Something went wrong..')

@app.route("/cleaning")
def cleanView(toast=""):
    return render_template('/cleaning.html', toast=toast, pumps=bar.pumps)

@app.route("/tools/clean", methods=['POST'])
def cleanAction():
    try:
        iding = request.form.get('iding')

        if iding == "":
            raise Exception()
        iding = int(iding)

        bar.pumps[iding].clean()
        bar.save_config('config')
        return cleanView('Pump ' + str(iding+1) + ' cleaned.')
    except:
        return cleanView('Something went wrong..')

@app.route("/crop", methods=['POST'])
def crop():
    from PIL import Image

    path = request.form.get('path');
    coords = (float(request.form.get('x')), float(request.form.get('y')), float(request.form.get('x2')), float(request.form.get('y2')))
    width = float(request.form.get('w'))
    name = request.form.get('name')

    image_obj = Image.open('static/' + path)
    print(coords)
    cropped_image = image_obj.crop(coords)
    cropped_image.save('static/pictures/'+name)
    delpath = os.path.dirname(__file__) + "/static/" + path
    os.remove(delpath)

    return jsonify({'error': 0})

def startFirefox():
    driver = webdriver.Firefox()
    driver.get("http://127.0.0.1:5000")

def startChrome():
    chrome_options = Options()
    chrome_options.add_argument("--kiosk")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("http://127.0.0.1:5000")

if __name__ == "__main__":
    t = Thread(target=startChrome)
    t.start()
    app.run(debug=False)
    #app.run(host='192.168.0.77', port=5000, debug=False)
    #app.run(host='10.2.211.39', port=5000, debug=False)
