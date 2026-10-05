from flask import Flask
from flask_login import current_user

from config import Config
from extensions import db, login_manager
from models import User, Setting


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.expert import expert_bp
    from blueprints.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(expert_bp)
    app.register_blueprint(student_bp)

    @app.context_processor
    def inject_globals():
        try:
            site_name = Setting.get("site_name", app.config["SITE_NAME"])
        except Exception:
            site_name = app.config["SITE_NAME"]
        return {"site_name": site_name, "current_user": current_user}

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/error.html", code=403,
                                message="You don't have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/error.html", code=404,
                                message="The page you're looking for doesn't exist."), 404

    @app.errorhandler(401)
    def unauthorized(e):
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
