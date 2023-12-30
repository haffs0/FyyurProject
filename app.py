#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
ma = Marshmallow(app)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120), unique=True)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(1000))

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120), unique=True)
    # genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(1000))
   
   
class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'),
        nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'),
        nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  artists = db.relationship('Artist', backref='show', lazy=True)
  venues = db.relationship('Venue', backref='show', lazy=True)


class ArtistSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Artist


class VenueSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Venue
         
class VenueGroupbySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Venue
        fields = ('state', 'city')

class ShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Show

    venues = ma.Nested(VenueSchema, only=("id", "name"))
    artists = ma.Nested(ArtistSchema, only=("id", "name", "image_link"))

class ArtistShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Show

    venues = ma.Nested(VenueSchema, only=("id", "name", "image_link"))
    artists = ma.Nested(ArtistSchema)

class VenueShowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Show

    venues = ma.Nested(VenueSchema)
    artists = ma.Nested(ArtistSchema, only=("id", "name", "image_link"))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  elif format == 'complete':
      format= "Y-m-d H:M:S"

  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  data = []

  venue = Venue.query.all()
  venue_schema = VenueSchema(many=True)
  output = venue_schema.dump(venue)

  venue = Venue.query.distinct(Venue.state).all()
  venue_schema = VenueGroupbySchema(many=True)
  output2 = venue_schema.dump(venue)
  
  for value in output2:
    for item in output:
      if item['state'] == value['state'] and item['city'] == value['city']:
        if 'venues' not in value.keys():
          value['venues'] = []
        value['venues'].append({'id': item['id'], 'name': item['name']})
   
    data.append(value)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search_results = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  venue_schema = VenueSchema(many=True)
  output = venue_schema.dump(search_results)

  response={
    "count": len(output),
    "data": output
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  error = False
  try:
    venue = Show.query.filter_by(venue_id=venue_id).all()
    venue_show_schema = VenueShowSchema(many=True)
    output = venue_show_schema.dump(venue)

    dic = {}
    dic["id"] = output[0]["venues"]["id"]
    dic["name"] = output[0]["venues"]["name"]
    # dic["genres"] = output[0]["venues"]["genres"]
    dic["address"] = output[0]["venues"]["address"]
    dic["city"] = output[0]["venues"]["city"]
    dic["state"] = output[0]["venues"]["state"]
    dic["phone"] = output[0]["venues"]["phone"]
    dic["website_link"] = output[0]["venues"]["website_link"]
    dic["facebook_link"] = output[0]["venues"]["facebook_link"]
    dic["seeking_talent"] = output[0]["venues"]["seeking_talent"]
    dic["seeking_description"] = output[0]["venues"]["seeking_description"]
    dic["image_link"] = output[0]["venues"]["image_link"]
    dic["past_shows"] = []
    dic["upcoming_shows"] = []

    for item in output:
      day = datetime.strptime(item["start_time"]+"+00:00", "%Y-%m-%dT%H:%M:%S+00:00")
      if day < datetime.now():
        dic["past_shows"].append({"artist_id":item["artists"]["id"], "artist_name":item["artists"]["name"], "artist_image_link":item["artists"]["image_link"], "start_time":item["start_time"]})
      else:
        dic["upcoming_shows"].append({"artist_id":item["artists"]["id"], "artist_name":item["artists"]["name"], "artist_image_link":item["artists"]["image_link"], "start_time":item["start_time"]})

    
    dic["past_shows_count"] = len(dic["past_shows"])
    dic["upcoming_shows_count"] = len(dic["upcoming_shows"])

  except Exception as e:
    if len(dic) != 0:
      error = True
    print(e)

  if error:
      abort(500)
  else:
      if len(dic) == 0:
        venue = Venue.query.get(venue_id)
        dic = VenueSchema().dump(venue)
        dic["past_shows_count"] = 0
        dic["upcoming_shows_count"] = 0
      return render_template('pages/show_venue.html', venue=dic)
    

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  error = False

  try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(venue)
      db.session.commit()
  except Exception as e:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      #abort(500)
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  else:
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
  return render_template('pages/home.html') 

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist = Artist.query.all()
  artist_schema = ArtistSchema(many=True)
  data = artist_schema.dump(artist)
 
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  search_results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  artist_schema = ArtistSchema(many=True)
  output = artist_schema.dump(search_results)

  response={
    "count": len(output),
    "data": output
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  error=False
  try:
    artist = Show.query.filter_by(artist_id=artist_id).all()
    artist_show_schema = ArtistShowSchema(many=True)
    output = artist_show_schema.dump(artist)

    dic = {}
    dic["id"] = output[0]["artists"]["id"]
    dic["name"] = output[0]["artists"]["name"]
    dic["city"] = output[0]["artists"]["city"]
    dic["state"] = output[0]["artists"]["state"]
    dic["phone"] = output[0]["artists"]["phone"]
    dic["website_link"] = output[0]["artists"]["website_link"]
    dic["facebook_link"] = output[0]["artists"]["facebook_link"]
    dic["seeking_venue"] = output[0]["artists"]["seeking_venue"]
    dic["seeking_description"] = output[0]["artists"]["seeking_description"]
    dic["image_link"] = output[0]["artists"]["image_link"]
    dic["past_shows"] = []
    dic["upcoming_shows"] = []

    for item in output:
      day = datetime.strptime(item["start_time"]+"+00:00", "%Y-%m-%dT%H:%M:%S+00:00")
      if day < datetime.now():
        dic["past_shows"].append({"venue_id":item["venues"]["id"], "venue_name":item["venues"]["name"], "venue_image_link":item["venues"]["image_link"], "start_time":item["start_time"]})
      else:
        dic["upcoming_shows"].append({"venue_id":item["venues"]["id"], "venue_name":item["venues"]["name"], "venue_image_link":item["venues"]["image_link"], "start_time":item["start_time"]})

    
    dic["past_shows_count"] = len(dic["past_shows"])
    dic["upcoming_shows_count"] = len(dic["upcoming_shows"])
  except Exception as e:
    print(e)
    if len(dic) != 0:
      error=True

  if error:
      abort(500)
  else:
      if len(dic) == 0:
        artist = Artist.query.get(artist_id)
        dic = ArtistSchema().dump(artist)
        dic["past_shows_count"] = 0
        dic["upcoming_shows_count"] = 0
      return render_template('pages/show_artist.html', artist=dic)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    artist_data = ArtistSchema().dump(artist)
    form = ArtistForm(obj=artist)
  except Exception as e:
    print(e)
  finally:
    return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
  
    db.session.commit()
  except Exception as e:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      #flash(u'An error occurred. Artist ' + form.name.data + ' information could not be updated.', 'error')
  else:
      flash('Artist ' + form.name.data + ' information was successfully updated!')
      return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    venue_data = VenueSchema().dump(venue)
    form = VenueForm(obj=venue)
  except Exception as e:
    print(e)
  finally:
    return render_template('forms/edit_venue.html', form=form, venue=venue_data)
  
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
  
    db.session.commit()
  except Exception as e:
      db.session.rollback()
      print(e)
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      #flash(u'An error occurred. Venue ' + form.name.data + ' information could not be updated.', 'error')
  else:
      flash('Venue ' + form.name.data + ' information was successfully updated!')
      return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  error = False

  try:
      artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
  except Exception as e:
      db.session.rollback()
      print(e)
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      #flash(u'An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')
  else:
      flash('Artist ' + form.name.data + ' was successfully listed!')
      return render_template('pages/home.html') 

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.distinct(Show.id).all()
  show_schema = ShowSchema(many=True)
  output = show_schema.dump(shows)
  results = [
    {
    'venue_id': v["venues"]["id"],
    "venue_name":v["venues"]["name"],
    "artist_id": v["artists"]["id"],
    "artist_name": v["artists"]["name"],
    "artist_image_link":v["artists"]["image_link"],
    "start_time":v["start_time"]
    } for v in output
  ]

  return render_template('pages/shows.html', shows=results)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  error = False
 
  try:
      artist = Artist.query.get(form.artist_id.data)
     
      venue = Venue.query.get(form.venue_id.data)

      show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data,
        artists=artist,
        venues=venue
      )
      db.session.add(show)
      db.session.commit()
  except Exception as e:
      print(e)
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      #flash(u'An error occurred. show could not be listed', 'error')
  else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      return render_template('pages/home.html') 

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#
def create_db():
    with app.app_context():
        db.create_all()

# Default port:
if __name__ == '__main__':
    # create_db()
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
