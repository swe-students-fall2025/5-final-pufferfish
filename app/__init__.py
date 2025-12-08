from flask import Flask
from app.config import Config
from app.extensions import mongo, login_manager, bcrypt
from app.services.user_service import UserService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set secret key for sessions
    import os
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    #  Extensions
    mongo.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return UserService.get_user_by_id(user_id)

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal Server Error: {str(error)}', exc_info=True)
        from flask import render_template, flash, redirect, url_for
        flash('An internal server error occurred. Please try again later.')
        return redirect(url_for('main.index'))

    # Blueprints - import all blueprints
    from app.views.auth_views import auth_bp
    from app.views.main_views import main_bp
    from app.views.resume_views import resume_bp
    from app.views.resume_form_views import resume_form_bp
    from app.views.profile_views import profile_bp
    from app.views.feed_views import feed_bp

    # Register all blueprints once
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(resume_form_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(feed_bp)

    # mongo
    mongo.db.resumes.create_index([
        ('$**', 'text')
    ])


    return app
