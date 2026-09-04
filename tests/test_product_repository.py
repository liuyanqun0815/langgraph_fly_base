from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sale_app.database.sqlalchemy_models import Base, Product


def test_product_model_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.add(
            Product(
                product_name="测试贷",
                product_priority=1,
                product_type=1,
                product_info="info",
            )
        )
        session.commit()
        row = session.query(Product).one()
        assert row.product_name == "测试贷"
