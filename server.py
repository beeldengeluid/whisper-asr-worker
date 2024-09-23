from app import create_app

# NOTE this file SHOULD make it backwards compatible with the existing supervisord config
# run this with: uwsgi --http 127.0.0.1:5304 --master -p 4 -w server:app
service = create_app()


if __name__ == '__main__':
    service.run(debug=True)
