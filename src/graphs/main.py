from dotenv import load_dotenv
from workflow import app

load_dotenv()

if __name__ == "__main__":
    question1 = "Veritabanındaki en son aya göre hesaplandığında, son 3 ayda en çok sipariş alan ilk 5 ürün kategorisi hangileridir ve toplam sipariş sayıları kaçtır?"

    response = app.invoke({"question": question1})
    print(response.get("generation"))