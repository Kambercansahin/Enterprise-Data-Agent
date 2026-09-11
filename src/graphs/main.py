from dotenv import load_dotenv
from workflow import graph

load_dotenv()

if __name__ == "__main__":
    question1 = "Müşteriler kargo teslimat süresi ve gecikmeler hakkında ne diyor?"

    response = graph.invoke({"question": question1})
    print(response.get("generation"))