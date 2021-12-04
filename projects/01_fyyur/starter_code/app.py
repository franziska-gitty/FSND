# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

from models import *
Migrate(app, db)


# # ----------------------------------------------------------------------------#
# # Filters.
# # ----------------------------------------------------------------------------#
#
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # displays the venues in a list
    areas = Venue.query.order_by(Venue.city).distinct(Venue.city)
    data = []
    for area in areas:
        venues_of_area = Venue.query.filter_by(city=area.city).all()
        venue_data = []
        for venue in venues_of_area:
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(Show.query.filter_by(venue_id=venue.id).filter(Show.date >
                                                                                         datetime.now()).all())
            })
        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })
    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search = request.form.get('search_term', '')

    all_found_venues = Venue.query.filter(Venue.name.ilike("%" + search + "%")).all()

    data = []
    for venue in all_found_venues:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(Show.query.filter_by(venue_id=venue.id).filter(Show.date >
                                                                                     datetime.now()).all())
        })
    response = {
        "count": len(all_found_venues),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # displays the venue page with the given venue_id
    venue = Venue.query.filter_by(id=venue_id).one()
    # if not join: shows_of_venue = venue.shows
    shows_of_venue = Show.query.join(Venue).filter(Show.venue_id == venue_id).all()
    data_past_shows = []
    data_upcoming_shows = []
    past_show_count = 0
    upcoming_show_count = 0

    for show in shows_of_venue:
        if show.date < datetime.now():
            artist = Artist.query.filter_by(id=show.artist_id).one()
            data_past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.date)
            })
            past_show_count += 1
        else:
            artist = Artist.query.filter_by(id=show.artist_id).one()
            data_upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.date)
            })
            upcoming_show_count += 1

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres[1:-1].split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": data_past_shows,
        "upcoming_shows": data_upcoming_shows,
        "past_shows_count": past_show_count,
        "upcoming_shows_count": upcoming_show_count
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)

    try:
        new_venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data,
                          address=form.address.data, phone=form.phone.data, genres=form.genres.data,
                          facebook_link=form.facebook_link.data, image_link=form.image_link.data,
                          website=form.website_link.data, seeking_talent=form.seeking_talent.data,
                          seeking_description=form.seeking_description.data)
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + form.name.data + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue_to_delete = Venue.query.filter_by(id=venue_id).one()
        db.session.delete(venue_to_delete)
        db.session.commit()
        flash('The Venue has been successfully deleted!')
    except():
        db.session.rollback()
        flash('Delete was unsuccessful. Try again!')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # displays all artists on a list
    all_artists = Artist.query.all()

    data = []

    for artist in all_artists:
        data.append({
            'id': artist.id,
            'name': artist.name,
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search = request.form.get('search_term', '')
    all_found_artists = Artist.query.filter(Artist.name.ilike("%" + search + "%")).all()

    data = []
    for artist in all_found_artists:
        data.append({
            'id': artist.id,
            'name': artist.name,
        })
    response = {
        "count": len(all_found_artists),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.filter_by(id=artist_id).one()

    shows_of_artist = Show.query.join(Venue).filter(Show.artist_id == artist_id).all()
    data_past_shows = []
    data_upcoming_shows = []
    past_show_count = 0
    upcoming_show_count = 0

    for show in shows_of_artist:
        if show.date < datetime.now():
            venue = Venue.query.filter_by(id=show.venue_id).one()
            data_past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.date)
            })
            past_show_count += 1
        else:
            venue = Venue.query.filter_by(id=show.venue_id).one()
            data_upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.date)
            })
            upcoming_show_count += 1

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres[1:-1].split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": data_past_shows,
        "upcoming_shows": data_upcoming_shows,
        "past_shows_count": past_show_count,
        "upcoming_shows_count": upcoming_show_count
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    artist = Artist.query.filter_by(id=artist_id).one()

    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.add(artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + form.name.data + ' was successfully edit!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    error = False
    venue = Venue.query.filter_by(id=venue_id).one()

    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + form.name.data + ' was successfully edit!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    error = False

    try:
        new_artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data,
                            phone=form.phone.data, genres=form.genres.data,
                            facebook_link=form.facebook_link.data, image_link=form.image_link.data,
                            website=form.website_link.data, seeking_venue=form.seeking_venue.data,
                            seeking_description=form.seeking_description.data)
        db.session.add(new_artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Show.query.all()
    data = []
    for show in shows:
        venue = Venue.query.filter_by(id=show.venue_id).one()
        artist = Artist.query.filter_by(id=show.artist_id).one()
        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.date)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    error = False

    try:
        new_show = Show(date=form.start_time.data, venue_id=form.venue_id.data,
                        artist_id=form.artist_id.data)
        db.session.add(new_show)
        db.session.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
