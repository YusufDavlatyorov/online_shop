from sqlalchemy import Column, Integer,String, DateTime,ForeignKey,BigInteger,create_engine,Numeric
from sqlalchemy.orm import declarative_base,relationship
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
link=os.getenv('link')
Base=declarative_base()
db_url=link

engine=create_engine(db_url)

class Users(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    tg_id=Column(BigInteger, unique=True)
    name=Column(String(150))

class Categories(Base):
    __tablename__='categories'
    id=Column(Integer,primary_key=True)
    title=Column(String(100))

class Products(Base):
    __tablename__='products'
    id=Column(Integer,primary_key=True)
    title=Column(String(100))
    description=Column(String((150)))
    price=Column(Numeric(10,2))
    photo_url=Column(String(300))
    stock=Column(Integer)
    category_id=Column(Integer,ForeignKey('categories.id'))
    created_at=Column(DateTime, default=datetime.now())

class Cart(Base):
    __tablename__='carts'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id', ondelete='cascade'))
    status=Column(String(20), default='active')
    created_at=Column(DateTime, default=datetime.now())


class CartItems(Base):
    __tablename__='cart_items'
    id=Column(Integer,primary_key=True)
    cart_id=Column(ForeignKey('carts.id', ondelete='cascade'))
    product_id=Column(ForeignKey('products.id', ondelete='cascade'))
    quantity=Column(Integer, nullable=False)


class Order(Base):
    __tablename__='orders'
    id=Column(Integer,primary_key=True)
    user_id=Column(ForeignKey('users.id', ondelete='cascade'))
    total_price=Column(Numeric(10,2))
    address=Column(String(200), nullable=None)
    created_at=Column(DateTime, default=datetime.now())

class OrderItems(Base):
    __tablename__='order_items'
    id=Column(Integer,primary_key=True)
    order_id=Column(ForeignKey('orders.id', ondelete='cascade'))
    product_id=Column(ForeignKey('products.id', ondelete='cascade'))
    quantity=Column(Integer, nullable=False)
    size=Column(String(250))




Base.metadata.create_all(engine)