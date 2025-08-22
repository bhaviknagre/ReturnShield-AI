from sqlalchemy.orm import Session
from models import Customer, Order


def seed(db: Session):
    if db.query(Customer).count() == 0:
        c1 = Customer(
            email="alice@example.com", name="Alice", total_orders=5, total_returns=1
        )
        c2 = Customer(
            email="bob@example.com", name="Bob", total_orders=2, total_returns=2
        )
        db.add_all([c1, c2])
        db.flush()

        o1 = Order(
            order_id="ORD-1001",
            customer_id=c1.id,
            sku="SKU123",
            size="M",
            color="Blue",
            status="delivered",
        )
        o2 = Order(
            order_id="ORD-1002",
            customer_id=c2.id,
            sku="SKU456",
            size="9",
            color="Black",
            status="delivered",
        )
        db.add_all([o1, o2])
        db.commit()
