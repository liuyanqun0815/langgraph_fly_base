# Copyright 2024-2026 liuyanqun
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
