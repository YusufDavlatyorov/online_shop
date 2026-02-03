from aiogram import filters, Dispatcher,Bot,F
from aiogram.types import(
    InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton,
    CallbackQuery,Message,BotCommand,FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State,StatesGroup
from db import Users,Categories,Products,Cart,CartItems,Order,OrderItems,engine
from sqlalchemy.orm import sessionmaker
Session=sessionmaker(bind=engine)
session=Session()
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
ai_ki=os.getenv('Token_G')
Token=os.getenv('Token')

from groq import Groq
client=Groq(api_key=ai_ki)



dp=Dispatcher()
admin=6922258296

comand=[
    BotCommand(command='start', description='registration and creating cart'),
    BotCommand(command='option', description='oportunaties of bot'),
    BotCommand(command='add_category', description='adding any new category'),
    BotCommand(command='add_product', description='adding any product'),
]

class Wait(StatesGroup):
    wait_for_cat_name=State()
    wait_for_product_title=State()
    wait_for_product_price=State()
    wait_for_product_category=State()
    wait_for_product_photo=State()
    wait_for_product_stock=State()
    wait_for_product_desc=State()
    wait_for_product_quantity=State()


@dp.message(filters.Command('add_category'))
async def adding_cat(message:Message,state:FSMContext):
    if message.from_user.id != admin:
        await message.answer('it can do just admin')
    else:
        await message.answer('Enter title of categoty')
        await state.set_state(Wait.wait_for_cat_name)

@dp.message(Wait.wait_for_cat_name)
async def fin_cat(message:Message, state:FSMContext):
    await state.update_data(title=message.text.strip())
    data=await state.get_data()
    category=session.query(Categories).filter_by(title=data['title']).first()
    if category:
        await message.answer('We have allready this category')
    else:
        cat=Categories(title=data['title'])
        session.add(cat)
        await message.answer('Category added succesfully!')
        session.commit()
        
    await state.clear()


@dp.message(filters.Command('add_product'))
async def add_product(message:Message,state:FSMContext):
    if message.from_user.id != admin:
        await message.answer('It can do just admin')
    else:
        await message.answer('Enter products name')
        await state.set_state(Wait.wait_for_product_title)

@dp.message(Wait.wait_for_product_title)
async def desc(message:Message,state:FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer('Enter products description')
    await state.set_state(Wait.wait_for_product_desc)



@dp.message(Wait.wait_for_product_desc)
async def add_title(message:Message,state:FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer('Enter products price')
    await state.set_state(Wait.wait_for_product_price)

@dp.message(Wait.wait_for_product_price)
async def add_price(message:Message,state:FSMContext):
    pric=float(message.text.strip())
    if pric>0:
            await state.update_data(price=pric)
            await message.answer('Enter product category')
            await state.set_state(Wait.wait_for_product_category)
    else:
        await message.answer('Price must be numeric for instance>>(99.90) and greater than 0')

@dp.message(Wait.wait_for_product_category)
async def add_category(message:Message,state:FSMContext):
    cataegory_name=message.text.strip()
    category=session.query(Categories).filter_by(title=cataegory_name).first()
    if not category:
        await message.answer('We dont have this type of category')
    else:
        await state.update_data(category_id=category.id)
        await message.answer('Enter url of photo')
        await state.set_state(Wait.wait_for_product_photo)


@dp.message(Wait.wait_for_product_photo)
async def add_categ(message:Message,state:FSMContext):
    await state.update_data(photo=message.text.strip())
    data=await state.get_data()
    product=Products(title=data['title'],
                     description=data['description'],
                     price=data['price'],
                     category_id=data['category_id'],
                     photo_url=data['photo'])
    session.add(product)
    await message.answer('Product added successfuly')
    session.commit()
    await state.clear()
    
@dp.message(filters.Command('start'))
async def regis(message:Message):
    user=session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if not user:
        us=Users(tg_id=message.from_user.id,name=message.from_user.username)
        session.add(us)
        session.commit()
        card=Cart(user_id=us.id)
        session.add(card)
        session.commit()
        await message.answer('You registered successfuly and yours first cart is created, for countinue please tap the -option- comand')
    else:
        await message.answer(f'Welcome back {user.name}! You have allready cart, for countinue please tap the -option- comand')

@dp.message(filters.Command('option'))
async def choice(message:Message):
    markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Category')],
            [KeyboardButton(text='Contacts'), KeyboardButton(text='My cart')]
        ]
    )
    await message.answer(text='chose a option', reply_markup=markup)

@dp.message(F.text=='Category')
async def category(message:Message):
    category=session.query(Categories).all()
    buttons=[]
    for c in category:
        buttons.append(
            [InlineKeyboardButton(
                text=f'{c.title}', callback_data=f'cat_{c.id}'
            )]
        )
    markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text='choose a category', reply_markup=markup)
    

@dp.callback_query(F.data.startswith('cat_'))
async def show_products(call:CallbackQuery):
    cat_id=int(call.data.split('_')[1])
    product=session.query(Products).filter_by(category_id=cat_id).all()
    if not product:
        await call.message.answer('No products in category yet')
        await call.answer()
    for p in product:
        markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Add to cart' , callback_data=f'prod_{p.id}')]
            ]
        )
        await call.message.answer_photo(
            photo=p.photo_url,
            caption=f'{p.title}\n {p.price}\n {p.description}',
            reply_markup=markup

        )
    await call.answer()

@dp.callback_query(F.data.startswith('prod_'))
async def add_to_cart(call:CallbackQuery):
    user_id=call.from_user.id
    product_id=int(call.data.split('_')[1])
    user=session.query(Users).filter_by(tg_id=user_id).first()
    cart=session.query(Cart).filter_by(user_id=user.id).first()
    cart_item=session.query(CartItems).filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        await call.message.answer('You have allready this product in your cart')
    else:
        cart_item=CartItems(cart_id=cart.id, product_id=product_id,quantity=0 )
        session.add(cart_item)
        await call.message.answer('Product added successfuly to your cart')
        session.commit()

    await call.answer()
    
@dp.message(F.text=='My cart')
async def category(message:Message):
    user=session.query(Users).filter_by(tg_id=message.from_user.id).first()
    cart=session.query(Cart).filter_by(user_id=user.id).first()
    items=session.query(CartItems).filter_by(cart_id=cart.id).all()
    if not items:
        await message.answer('Your cart is empty yet')
    
    buttons=[]
    for i in items:
        product=session.query(Products).filter_by(id=i.product_id).first()
        buttons.append(
            [InlineKeyboardButton(text=f'title: {product.title}\n price: {product.price}\n description: {product.description}', callback_data=f'cartitem_{i.id}')]
            )
    markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer_photo(
        photo=product.photo_url,
        reply_markup=markup
    )
    session.commit()

@dp.callback_query(F.data.startswith('cartitem_'))
async def order_or_delete(call:CallbackQuery):
    cart_item_id=int(call.data.split('_')[1])
    markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='DELETE',callback_data=f'delete_{cart_item_id}'),
             InlineKeyboardButton(text='ORDER', callback_data=f'order_{cart_item_id}')]
        ]
    )
    await call.message.answer('What do you want do with this product', reply_markup=markup)
    await call.answer()

@dp.callback_query(F.data.startswith('delete_'))
async def delete_from_cart(call:CallbackQuery):
    delete_id=int(call.data.split('_')[1])
    cart_item=session.query(CartItems).filter_by(id=delete_id).first()
    if not cart_item:
        await call.message.answer('product not found')
        await call.answer()
    session.delete(cart_item)
    session.commit()
    
    await call.message.answer('Product deleted from cart')
    await call.answer()

@dp.callback_query(F.data.startswith('order_'))
async def delete_from_cart(call:CallbackQuery,state:FSMContext):
    cart_id=int(call.data.split('_')[1])
    await state.update_data(cart_id=cart_id)
    await call.message.answer('Enter quantity of product(it must be greater than 0)')
    await state.set_state(Wait.wait_for_product_quantity)
    await call.answer()

@dp.message(Wait.wait_for_product_quantity)
async def order_from_cart(message:Message,state:FSMContext):
    quan=int(message.text.strip())
    if quan<=0:
        await message.answer('Please enter a number greater than 0 !')
    else:
        data=await state.get_data()
        cart_item_id=data['cart_id']
        cart_item=session.query(CartItems).filter_by(id=cart_item_id).first()
        if not cart_item:
            await message.answer('Cart product not found')
            await state.clear()

        cart=session.query(Cart).filter_by(id=cart_item.cart_id).first()
        user=session.query(Users).filter_by(id=cart.user_id).first()
        product=session.query(Products).filter_by(id=cart_item.product_id).first()
        total=product.price*quan
        order=Order(user_id=user.id, total_price=total)
        session.add(order)
        session.commit()
        order_item=OrderItems(
            order_id=order.id,
            product_id=product.id,
            quantity=quan,
        )
        session.add(order_item)
        session.delete(cart_item)
        session.commit()
        await message.answer(f'Order created!\n'f'Product:{product.title}\n'f'Quantity:{quan}\n'f'Total_price:{total}')
        await message.bot.send_message(
                chat_id=admin,
                text=(f"New order!\n"
                    f"User: {user.name}\n"
                    f"Product: {product.title}\n"
                    f"Quantity: {quan}\n"
                    f"Total: {total}"
                )
            )       
        await state.clear()

@dp.message(F.text=='Contacts')
async def category(message:Message):
    await message.answer('Our numbers:\n+992711111111\n+992006909090\n+992071717171')




@dp.message()
async def ai_chat(message:Message):
    user_text=message.text
    print(user_text)

    response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": 'you must answer in tajik about our shop. our shop is big shop with a lot of category and products'},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=500,
        )

    ai_answer = response.choices[0].message.content
    await message.answer(ai_answer)


async def main():
    bot=Bot(token=Token)
    await bot.set_my_commands(comand)
    await dp.start_polling(bot)

if __name__=='__main__':
    asyncio.run(main())