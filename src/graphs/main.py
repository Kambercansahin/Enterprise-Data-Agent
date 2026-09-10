from dotenv import load_dotenv
from workflow import app

load_dotenv()

if __name__ == "__main__":
    question1 = "Müşteriler kargo teslimat süresi ve gecikmeler hakkında ne diyor?"

    response = app.invoke({"question": question1})
    print(response.get("generation"))