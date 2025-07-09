from appPackage import create_app, db

app = create_app()

# with app.app_context():
#     db.create_all()
# with app.app_context():
#     db.create_all()
#     print("All tables recreated.")

if __name__ == "__main__":
    app.run(debug=True)
