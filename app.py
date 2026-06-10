import os
from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager
from models import User
from flask_apscheduler import APScheduler
from backup import perform_backup

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Scheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    
    # Schedule Backup (Every 48 hours = 2880 minutes, or use interval days=2)
    @scheduler.task('interval', id='do_backup', days=2)
    def scheduled_backup():
        perform_backup(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp



    
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8007, debug=True)
