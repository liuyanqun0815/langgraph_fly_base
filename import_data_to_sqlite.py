import json

import dotenv

dotenv.load_dotenv()

from sale_app.database.session import engine, get_db_session
from sale_app.database.sqlalchemy_models import Base, Product


def load_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def import_data(data):
    with get_db_session() as session:
        for item in data:
            session.add(Product(**item))
        session.commit()


def main():
    Base.metadata.create_all(bind=engine)
    data = load_data("sale_app/migrations/init_sqllite.json")
    import_data(data)


if __name__ == "__main__":
    main()
