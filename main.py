from math import ceil
import os
from flask import Flask, url_for, render_template, redirect, request, session
from markupsafe import escape
import mysql.connector
import hashlib

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="akhparfum"
)


cursor = db.cursor(dictionary=True)

app = Flask(__name__)
app.secret_key = 'hezeyanTest'


def categories():
    sql = "SELECT * FROM category ORDER BY category_id"
    cursor.execute(sql)
    cats = cursor.fetchall()
    return cats


def carouselItems():
    sql = "SELECT * FROM carousel WHERE carousel_status = %s ORDER BY carousel_id DESC"
    cursor.execute(sql, (1,), )
    items = cursor.fetchall()
    return items

def discountCalc(mainPrice, discount):
    lastPrice = mainPrice - (mainPrice * 0.01 * discount)
    return lastPrice


def pagesCount(sql, s, viewCount):
    cursor.execute(sql, (s,),)
    pageCount = cursor.fetchone()
    return ceil(pageCount['id'] / viewCount)


def convertToBinaryData(filename):
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData



from datetime import date
today = date.today()
day = today.day
month_word = today.strftime("%B")
year = today.year
#today's date
todays_date = str(day)+' '+month_word+' '+str(year)

app.config["UPLOAD_FOLDER"] = "static/img"
app.use_static_route = True




app.jinja_env.globals.update(categories=categories, carouselItems=carouselItems, discountCalc=discountCalc, pagesCount=pagesCount)

@app.route('/')
def home():
    sql= "SELECT * FROM fragrances "\
        "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
        "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
        "WHERE fragrance_instock = 1 "\
        "ORDER BY fragrance_id DESC LIMIT 8 "
    cursor.execute(sql)
    fragrances = cursor.fetchall()
    return render_template('index.html', fragrances=fragrances)



@app.route('/category/<url>/<count>')
def category(url,count):
    sql = "SELECT * FROM category WHERE category_url = %s"
    cursor.execute(sql, (url,))
    cat = cursor.fetchone()
    if cat:

        sql= "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "WHERE category_id = %s AND fragrance_instock=1 "\
            "ORDER BY fragrance_id DESC LIMIT %s,%s"
        limitCount = 0
        viewCount = 16
        if int(count) != 1:
            limitCount = (int(count)*viewCount)-viewCount
        cursor.execute(sql, (cat['category_id'],limitCount, viewCount, ), )
        fragrances = cursor.fetchall()

        page=pagesCount(("SELECT COUNT(fragrance_id) as id FROM fragrances INNER JOIN category ON category.category_id = fragrances.fragrance_category WHERE category_url=%s AND fragrance_instock=1 "),url, viewCount)
        if int(count) > page:
            return render_template('not-found.html')  
        else:
            return render_template('category.html', category=cat, url=url, fragrances=fragrances, count=count, viewCount=viewCount)
    else:
        return render_template('not-found.html')


@app.route('/perfume/<url>')
def perfume(url):
    sql= "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "WHERE fragrance_url = %s AND fragrance_instock=1 "\
            "ORDER BY fragrance_id DESC"
    cursor.execute(sql, (url,) ,)
    fragrance = cursor.fetchone()

    if fragrance:
        sql= "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "WHERE brand_id = %s AND fragrance_id != %s AND fragrance_instock=1 "\
            "ORDER BY fragrance_id DESC LIMIT 4"
        cursor.execute(sql, (fragrance['brand_id'], fragrance['fragrance_id'], ), )
        perfumes = cursor.fetchall()
        

        return render_template('detail.html', fragrance=fragrance, perfumes=perfumes)
    else:
        return render_template('not-found.html')



@app.route('/shop/<url>')
def shop(url):
    sql= "SELECT * FROM fragrances "\
        "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
        "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
        "WHERE fragrance_instock = 1 "\
        "ORDER BY fragrance_id DESC LIMIT %s,%s"
    limitCount = 0
    viewCount = 16
    if int(url) != 1:
        limitCount = (int(url)*viewCount)-viewCount
    
    cursor.execute(sql, (limitCount, viewCount, ),)
    fragrances = cursor.fetchall()

    page = pagesCount("SELECT COUNT(fragrance_id) as %s FROM fragrances WHERE fragrance_instock=1 ", "id", viewCount)
    if int(url) > page:
        return render_template('not-found.html') 
    else:
        return render_template('shop.html', fragrances=fragrances, viewCount=viewCount, url=url)
    

@app.route('/axi', methods=['GET', 'POST'])
def axi():
    if 'user_id' in session:
        return redirect(url_for('axipanel'))
    else:
        error = ""
        if request.method == 'POST':
            if request.form['email'] == '':
                error = 'Please enter email Axi!'
            elif request.form['password'] == '':
                error = 'Please enter password Axi!'
            else:
                sql = "SELECT * FROM users WHERE user_mail = %s && user_pass = %s "
                cursor.execute(sql,(request.form['email'], hashlib.md5(request.form['password'].encode()).hexdigest(),))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user['user_id']
                else:
                    error = 'We can\'t find you Axi'
        return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/axi-panel')
def axipanel():
    if 'user_id' in session:
        sqlUser = "SELECT * FROM users WHERE user_id = %s "
        cursor.execute(sqlUser, (session['user_id'], ),)
        user = cursor.fetchone()

        countSql = "SELECT COUNT(fragrance_id) as id FROM fragrances WHERE fragrance_instock=1"
        cursor.execute(countSql)
        count = cursor.fetchone()
        fragranceCount= count['id']

        allCountSql = "SELECT COUNT(fragrance_id) as id FROM fragrances"
        cursor.execute(allCountSql)
        allCount = cursor.fetchone()
        fragranceAllCount = allCount['id']

        if user:
            sql = "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "ORDER BY fragrance_id DESC "
            cursor.execute(sql)
            fragrances = cursor.fetchall()

            return render_template('axi-panel.html', user=user, fragrances=fragrances, fragranceCount=fragranceCount, fragranceAllCount=fragranceAllCount)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('axi'))


@app.route('/axi-panel/edit/<url>')
def editDetails(url):
        session['fragrance_url'] = url
        if 'user_id' in session:
            sql = "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "WHERE fragrance_url = %s "
            cursor.execute(sql, (url,),)
            fragrance = cursor.fetchone()

            sqlBrands = "SELECT * FROM brands"
            cursor.execute(sqlBrands)
            brands = cursor.fetchall()
            
            sqlUser = "SELECT * FROM users WHERE user_id = %s "
            cursor.execute(sqlUser, (session['user_id'], ),)
            user = cursor.fetchone()

            if fragrance:

                return render_template('edit.html', fragrance=fragrance, user=user, url=url, brands=brands)
            else:
                return redirect(url_for('axipanel')) 
        else:
            return redirect(url_for('home'))
   

@app.route('/axi-panel/edit/', methods=['GET', 'POST'])
def edit():
    if 'user_id' in session:

        if request.method == 'POST':
            name = request.form['name']
            brand = int(request.form['brand'])
            category = int(request.form['category'])
            desc = request.form['desc']
            formUrl = request.form['url']
            price = int(request.form['price'])
            price2 = int(request.form['price2'])
            price3 = int(request.form['price3'])
            discount = int(request.form['discount'])
            status = int(request.form['status'])


            thumb_file = request.files['file']
            thumb_file_name = thumb_file.filename
            thumb_file.save(os.path.join(app.config['UPLOAD_FOLDER'], thumb_file_name))
            thumb_file_name = "img/" + thumb_file_name


            cursor.execute("UPDATE fragrances SET fragrance_title=%s, fragrance_brand=%s, fragrance_category=%s, fragrance_url=%s,"\
            "fragrance_thumb=%s, fragrance_desc=%s, fragrance_price=%s, fragrance_price2=%s, fragrance_price3=%s, fragrance_discount=%s, "\
            "fragrance_instock=%s WHERE fragrance_url = %s ", (name, brand, category, formUrl, thumb_file_name, desc, price, price2, price3, discount, status,  session['fragrance_url']),)
            db.commit()
            return redirect(url_for('axipanel'))

        else: return redirect(url_for('axipanel'))
    else:
        return redirect(url_for('axi'))


@app.route('/axi-panel/add-panel')
def addfragrance():
    if 'user_id' in session:
        sqlUser = "SELECT * FROM users WHERE user_id = %s "
        cursor.execute(sqlUser, (session['user_id'], ),)
        user = cursor.fetchone()

        sqlBrands = "SELECT * FROM brands"
        cursor.execute(sqlBrands)
        brands = cursor.fetchall()

        return render_template('add-fragrance.html', user=user, brands=brands)
    else:
        return redirect(url_for('axipanel'))

@app.route('/axi-panel/add', methods=['GET', 'POST'])
def registerfragrance():
    if 'user_id' in session:

        if request.method == 'POST':
            name = request.form['name']
            brand = int(request.form['brand'])
            category = int(request.form['category'])
            desc = request.form['desc']
            formUrl = request.form['url']
            price = int(request.form['price'])
            price2 = int(request.form['price2'])
            price3 = int(request.form['price3'])
            discount = int(request.form['discount'])
            status = int(request.form['status'])


            thumb_file = request.files['file']
            thumb_file_name = thumb_file.filename
            thumb_file.save(os.path.join(app.config['UPLOAD_FOLDER'], thumb_file_name))
            thumb_file_name = "img/" + thumb_file_name


            cursor.execute("INSERT INTO fragrances fragrance_title=%s, fragrance_brand=%s, fragrance_category=%s, fragrance_url=%s,"\
            "fragrance_thumb=%s, fragrance_desc=%s, fragrance_price=%s, fragrance_price2=%s, fragrance_price3=%s, fragrance_discount=%s, "\
            "fragrance_instock=%s", (name, brand, category, formUrl, thumb_file_name, desc, price, price2, price3, discount, status),)
            db.commit()
            return redirect(url_for('axipanel'))

        else: return redirect(url_for('axipanel'))
    else:
        return redirect(url_for('axi'))


@app.route('/axi-panel/brand-panel/', methods=['GET', 'POST'])
def brandpanel():
    if 'user_id' in session:
        sqlUser = "SELECT * FROM users WHERE user_id = %s "
        cursor.execute(sqlUser, (session['user_id'], ),)
        user = cursor.fetchone()

        sql="SELECT * FROM brands ORDER BY brand_id DESC"
        cursor.execute(sql)
        brands = cursor.fetchall()

        return render_template('brand-panel.html', user=user, brands=brands)
    else:
        return redirect(url_for('axi'))
    
@app.route('/axi-panel/brand-update/<id>', methods=['GET', 'POST'])
def updatebrand(id):
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        status = int(request.form['status'])
        id = int(id)

        cursor.execute("UPDATE brands SET brand_title=%s, brand_desc=%s, brand_status=%s WHERE brand_id=%s", (title, desc, status, id))
        db.commit();
        return redirect(url_for('brandpanel'))
        


@app.route('/axi-panel/add-brand', methods=['GET', 'POST'])
def addbrand():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        status = int(request.form['status'])

        cursor.execute("INSERT INTO brands (brand_title, brand_desc, brand_status) VALUES (%s, %s, %s)",
                            (title, desc, status,))
        db.commit()

        return redirect(url_for('brandpanel'))


@app.route('/axi-panel/slider')
def slider():
    if 'user_id' in session:
        sqlUser = "SELECT * FROM users WHERE user_id = %s "
        cursor.execute(sqlUser, (session['user_id'], ),)
        user = cursor.fetchone()


        sql="SELECT * FROM carousel ORDER BY carousel_id DESC"
        cursor.execute(sql)
        sliders = cursor.fetchall()

        return render_template('slider.html', user=user, sliders=sliders)
    else:
        return redirect(url_for('axi'))

@app.route('/axi-panel/slider-control/<id>', methods=['GET', 'POST'])
def slidercontrol(id):
    if 'user_id' in session:

        if request.method == 'POST':
            title = request.form['title']
            second = request.form['second']
            status = int(request.form['status'])


            slider_file = request.files['file']
            slider_file_name = slider_file.filename
            slider_file.save(os.path.join(app.config['UPLOAD_FOLDER'], slider_file_name))
            slider_file_name = "img/" + slider_file_name


            cursor.execute("UPDATE carousel SET carousel_title=%s, carousel_second=%s, carousel_image=%s, carousel_status=%s WHERE carousel_id=%s ", (title, second, slider_file_name, status, id))
            db.commit()
            return redirect(url_for('slider'))

        else: return redirect(url_for('axi'))
    else:
        return redirect(url_for('axi'))


@app.route('/axi-panel/slider-add', methods=['GET', 'POST'])
def slideradd():
    if 'user_id' in session:

        if request.method == 'POST':
            title = request.form['title']
            second = request.form['second']
            status = int(request.form['status'])


            slider_file = request.files['file']
            slider_file_name = slider_file.filename
            slider_file.save(os.path.join(app.config['UPLOAD_FOLDER'], slider_file_name))
            slider_file_name = "img/" + slider_file_name


            cursor.execute("INSERT INTO carousel (carousel_title, carousel_second, carousel_image, carousel_status) VALUES (%s, %s, %s, %s)",
                            (title, second, slider_file_name, status,))
            db.commit()
            return redirect(url_for('slider'))

        else: return redirect(url_for('axi'))
    else:
        return redirect(url_for('axi'))


@app.route('/axi-panel/delete-panel')
def deletepanel():
    if 'user_id' in session:
        sqlUser = "SELECT * FROM users WHERE user_id = %s "
        cursor.execute(sqlUser, (session['user_id'], ),)
        user = cursor.fetchone()

        sql= "SELECT * FROM fragrances "\
            "INNER JOIN brands ON brands.brand_id = fragrances.fragrance_brand "\
            "INNER JOIN category ON category.category_id = fragrances.fragrance_category "\
            "ORDER BY fragrance_id DESC"
        cursor.execute(sql)
        fragrances = cursor.fetchall()

        sqlBrand = "SELECT * FROM brands ORDER BY brand_id DESC"
        cursor.execute(sqlBrand)
        brands = cursor.fetchall()

        return render_template('delete-panel.html', user=user, fragrances=fragrances, brands=brands)
    else:
        return redirect(url_for('axi'))

@app.route('/axi-panel/delete/', methods=['GET', 'POST'])
def delete():
    sql = "DELETE FROM fragrances WHERE fragrance_id=%s "
    cursor.execute(sql, ( int(request.form['fragrances']), ))
    db.commit()
    return redirect(url_for('axipanel'))

@app.errorhandler(404)
def not_found(error):
    return render_template('not-found.html'), 404