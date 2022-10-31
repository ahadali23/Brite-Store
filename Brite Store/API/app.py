from flask import Flask, render_template, request, session, url_for, redirect
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'random string'
CORS(app)
mysql = MySQL(app) 

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'assort123.'
app.config['MYSQL_DB'] = 'britestore'
app.config['MYSQL_HOST'] = 'localhost'

def getLoginDetails():
    cur = mysql.connection.cursor()
    if 'email' not in session:
        loggedIn = False
        firstName = ''
        noOfItems = 0
    else:
        loggedIn = True
        cur.execute("SELECT userID, UPPER(fName) FROM users WHERE email = '" + session['email'] + "'")
        uID, firstName = cur.fetchone()
        cur.execute("SELECT count(productID) FROM cart WHERE userID = " + str(uID))
        noOfItems = cur.fetchone()[0]
    cur.close()
    return (loggedIn, firstName, noOfItems)

@app.route("/")
def provideHome():
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template('index.html', loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/getcheckout",  methods = ['GET','POST'])
def Checkout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    cur = mysql.connection.cursor()
    cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
    userId = cur.fetchone()[0]
    cur.execute("SELECT product.productID, product.name, product.price,product.des, product.image_ FROM product, cart WHERE product.productID = cart.productID AND cart.userID = " + str(userId))
    products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
        print(row)
        cur.execute('''INSERT INTO `britestore`.`orders` (productID,userID) VALUES (%s, %s)''',(row[0],userId) )
    cur.execute("DELETE FROM cart WHERE userID = " + str(userId))
    mysql.connection.commit()
    return redirect(url_for('provideHome'))

@app.route("/checkout")
def provideCheckout():
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template('checkout.html', loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/login")
def provideLogin():
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template('login.html', loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/products")
def products():
    loggedIn, firstName, noOfItems = getLoginDetails()
    cur = mysql.connection.cursor()
    cur.execute('SELECT productId, name, price, des, image_ FROM product')
    itemData = cur.fetchall()
    cur.close()
    return render_template('products.html',loggedIn=loggedIn, firstName=firstName, itemData=itemData, noOfItems=noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('provideLogin'))
    else:
        productId = int(request.args.get('productId'))
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID FROM users WHERE email = '" + session['email'] + "'")
        userId = cur.fetchone()[0]
        cur.execute('''INSERT INTO `britestore`.`cart` (productID,userID) VALUES (%s, %s)''',(productId,userId) )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('products'))

@app.route("/yourcart")
def cart():
    if 'email' not in session:
        return redirect(url_for('provideLogin'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    cur = mysql.connection.cursor()
    cur.execute("SELECT userID FROM users WHERE email = '" + session['email'] + "'")
    uID = cur.fetchone()[0]
    cur.execute("SELECT product.productID, product.name, product.price, product.des FROM product, cart WHERE product.productID = cart.productID AND cart.userID = " + str(uID))
    products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('provideLogin'))
    email = session['email']
    productId = int(request.args.get('productId'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT userID FROM users WHERE email = '" + email + "'")
    userId = cur.fetchone()[0]
    try:
        cur.execute("DELETE FROM cart WHERE userID = " + str(userId) + " AND productID = " + str(productId))
        mysql.connection.commit()
    except:
        mysql.connection.rollback()
    cur.close()
    return redirect(url_for('cart'))

@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    cur = mysql.connection.cursor()
    cur.execute('SELECT productId, name, price, des FROM product WHERE productId = ' + productId)
    productData = cur.fetchone()
    cur.close()
    return render_template("productDes.html", data=productData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/getRegister" , methods = ['POST'])
def insertRecord():
    data = request.form
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO `britestore`.`users` ( `fName`, `lName`, `email`, `password`) VALUES (%s, %s, %s, %s)", [ data['fName'], data['lName'], data['email'], data['password']] )
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('provideLogin'))

@app.route("/getLogin", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('provideHome'))
        else:
            error = 'Invalid UserId / Password'
            return "Not Successfully"

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('provideHome'))

def is_valid(email, password):
    cur = mysql.connection.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == password:
            return True
    return False



if __name__ == '__main__':
    app.run(debug=True)