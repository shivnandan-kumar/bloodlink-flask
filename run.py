import os

from app import create_app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=app.config.get("DEBUG", False), port=port)
