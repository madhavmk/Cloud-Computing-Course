from waitress import serve
import temp_app
serve(temp_app.app, host='0.0.0.0', port=80)

