from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from random import choice
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

##Connect to Database.
uri = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return {self.name}

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    cafe_list = Cafe.query.all()
    return render_template("index.html", cafes=cafe_list, header='ALL CAFES')


@app.route('/random')
def random_cafe():
    all_data = Cafe.query.all()
    row = choice(all_data)
    return jsonify(cafe=row.to_dict())


@app.route('/all')
def all_cafes():
    cafes = Cafe.query.all()
    return jsonify(cafes=[cafe.to_dict() for cafe in cafes])


@app.route('/cafe/<int:cafe_id>/<cafe_name>')
def show_cafe(cafe_id, cafe_name):
    cafe_to_show = Cafe.query.get(cafe_id)
    if cafe_to_show and cafe_to_show.name == cafe_name:
        return render_template('cafe.html', cafe=cafe_to_show)
    else:
        return jsonify(error={"Not Found": "Sorry the cafe was not found in the database."}), 404


@app.route('/search')
def search():
    query_location = request.args.get("loc")
    cafes = db.session.query(Cafe).filter_by(location=query_location.title()).all()
    if cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})


@app.route('/search-results')
def search_results():
    query_location = request.args.get("loc")
    if query_location == '':
        return redirect(url_for('home'))
    else:
        cafes = db.session.query(Cafe).filter_by(location=query_location.title()).all()
        if cafes:
            heading = query_location.upper()
            not_found = False
        else:
            heading = f'NO CAFES FOUND IN {query_location.upper()}'
            not_found = True
        return render_template('index.html', cafes=cafes, header=heading, not_found=not_found)


@app.route('/add', methods=['POST'])
def add():
    new_cafe = Cafe(name=request.args.get("name"),
                    map_url=request.args.get("map_url"),
                    img_url=request.args.get("img_url"),
                    location=request.args.get("loc"),
                    seats=request.args.get("seats"),
                    has_toilet=bool(request.args.get("toilet")),
                    has_wifi=bool(request.args.get("wifi")),
                    has_sockets=bool(request.args.get("sockets")),
                    can_take_calls=bool(request.args.get("calls")),
                    coffee_price=request.args.get("price"), )
    db.create_all()
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


@app.route('/add-cafe/<edit>/<int:id>', methods=['GET', 'POST'])
def add_cafe(edit, id):
    if id > 0:
        cafe_to_edit = Cafe.query.get(id)
    else:
        cafe_to_edit = None
    if request.method == 'GET':
        if edit == 'y':
            header = 'Edit Cafe'
            btn = 'Save Edits'
        else:
            header = 'Add Cafe'
            btn = 'Add Cafe'
        return render_template('add-cafe.html', header=header, cafe=cafe_to_edit, btn=btn)
    elif request.method == 'POST':
        if edit != 'y':
            new_cafe = save_cafe()
            return redirect(url_for('show_cafe', cafe_id=new_cafe.id, cafe_name=new_cafe.name))
        else:
            save_edit(cafe_to_edit)
            return redirect(url_for('show_cafe', cafe_id=id, cafe_name=cafe_to_edit.name))


@app.route('/update-price/<int:cafe_id>', methods=['PATCH'])
def update_price(cafe_id):
    cafe_to_update = Cafe.query.get(cafe_id)
    if cafe_to_update:
        cafe_to_update.coffee_price = request.args.get("price")
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the cafe price."})
    else:
        return jsonify(error={"Not Found": "Sorry the cafe with that id was not found in the database."}), 404


@app.route('/report-closed/<int:cafe_id>', methods=['DELETE'])
def delete(cafe_id):
    cafe_to_delete = Cafe.query.get(cafe_id)
    if request.args.get('api_key') == os.environ.get('API-KEY'):
        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe"}), 200
        else:
            return jsonify(error={"Not Found": "Sorry the cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Sorry that's not allowed."}), 403


def save_edit(cafe):
    cafe.coffee_price = request.form.get("price")
    cafe.map_url = request.form.get("map_url")
    cafe.img_url = request.form.get("img_url")
    cafe.location = request.form.get("loc").title()
    cafe.seats = request.form.get("seats")
    # checkbutton(btn_list=['wifi', 'toilet', 'sockets', 'calls'], par_list=[cafe.has_wifi, cafe.has_toilet, cafe.has_sockets, cafe.can_take_calls])
    if request.form.get("wifi") == 'on':
        cafe.has_wifi = True
    else:
        cafe.has_wifi = False
    if request.form.get("toilet") == 'on':
        cafe.has_toilet = True
    else:
        cafe.has_toilet = False
    if request.form.get("sockets") == 'on':
        cafe.has_sockets = True
    else:
        cafe.has_sockets = False
    if request.form.get("calls") == 'on':
        cafe.can_take_calls = True
    else:
        cafe.can_take_calls = False

    db.session.commit()


def save_cafe():
    if request.form.get("wifi") == 'on':
        wifi = True
    else:
        wifi = False
    if request.form.get("toilet") == 'on':
        toilet = True
    else:
        toilet = False
    if request.form.get("sockets") == 'on':
        sockets = True
    else:
        sockets = False
    if request.form.get("calls") == 'on':
        calls = True
    else:
        calls = False

    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc").title(),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("price"),
        has_toilet=toilet,
        has_wifi=wifi,
        has_sockets=sockets,
        can_take_calls=calls,
        )
    db.create_all()
    db.session.add(new_cafe)
    db.session.commit()

    return new_cafe

# def checkbutton(btn_list, par_list):
#     n = 0
#     for btn in btn_list:
#         if request.form.get(btn) == 'on':
#             par_list[n] = 'True'
#         else:
#             par_list[n] = False
#         n += 1






## HTTP POST - Create Record

## HTTP PUT/PATCH - Update Record

## HTTP DELETE - Delete Record


if __name__ == '__main__':
    app.run(debug=True)
