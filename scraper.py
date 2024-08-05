import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

car_makes = ['Audi', 'Cupra', 'BMW', 'Ford', 'Mercedes-Benz', 'Opel', 'Renault', 'Volkswagen',
             'Volvo', 'Toyota', 'Skoda', 'Peugeot',
             'Hyundai', 'Kia', 'Nissan', 'Citroen', 'Dacia', 'Fiat', 'Honda', 'Mazda',
             'Mitsubishi', 'Seat', 'Suzuki', 'Chevrolet',
             'Jeep', 'Land Rover', 'Mini', 'Porsche', 'Subaru', 'Smart', 'Jaguar',
             'Lexus', 'Alfa Romeo', 'Chrysler', 'Daewoo', 'Dodge',
             'Hummer', 'Infiniti', 'Isuzu', 'Lancia', 'Saab', 'SsangYong',
             'Tesla', 'Acura', 'Cadillac','Ferrari',
             'Lamborghini', 'Lotus', 'Maserati', 'MG',
             'Rolls-Royce', 'Bentley', 'Bugatti',
             'Lada', 'Lancia', 'Lincoln',
             'Maybach', 'McLaren', 'Aston Martin', 'Genesis', "GMC", 'Ram']
baseurl = 'https://autovit.ro/autoturisme'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}
productLinks = []

try:
    uri = "DBURI"
    client = MongoClient(uri)
    client.admin.command("ping")
    db = client['vehi-trader-db']
    collection = db['cars']
    print("Connected successfully")

    for x in range(301, 400):
        r = requests.get(f'{baseurl}?page={x}')
        soup = BeautifulSoup(r.content, 'lxml')
        productList = soup.findAll('div', class_='ooa-r53y0q esqdut111')

        for item in productList:
            for link in item.findAll('a', href=True):
                if('anunt' in link['href']):
                    productLinks.append(link['href'])


    productLinks = list(dict.fromkeys(productLinks))
    productLinks = [link for link in productLinks if 'anunt' in link]
    print("Number of links: ", len(productLinks))

    for link in productLinks:
        try:
            r = requests.get(link, headers=headers)
            data = {}
            soup = BeautifulSoup(r.content, 'lxml')
            print("processing: ")

            # Extracting price
            price_element = soup.find('h3', class_="offer-price__number e1mlrgts4 ooa-1jtct0k er34gjf0")
            if price_element:
                price_str = price_element.get_text(strip=True)
                cleaned_price_str = price_str.replace(" ", "").replace(",", ".")
                price_float = float(cleaned_price_str)
                data['price'] = price_float
            else:
                data['price'] = None

            # Extracting other information
            items = soup.find_all('div', class_='ooa-162vy3d e130ulp53')
            for item in items:
                key_element = item.find('p', class_='e130ulp54 ooa-12b2ph5')
                if key_element:
                    key = key_element.get_text(strip=True)
                    value_tag = item.find('p', class_='e4cq37s0 ooa-1pe3502 er34gjf0') or item.find('a', class_='e4cq37s1 ooa-1ftbcn2')
                    if value_tag:
                        value = value_tag.get_text(strip=True)
                        # Strip non-numeric characters and convert to appropriate numeric types
                        if key == "Km" or key == "Putere" or key == "Capacitate cilindrica":
                            value = int(''.join(filter(str.isdigit, value)))
                        data[key] = value
                        if key == "Capacitate cilindrica":
                            data[key] = int(data[key]/10)
                        if key == "Anul producției":
                            data[key] = int(data[key])
                    else:
                        data[key] = None


            # Mapping dictionary to standardize keys
            mapping = {
                "Marca": "make",
                "Model": "model",
                "price": "price",
                "Versiune": "version",
                "Generatie": "generation",
                "Anul producției": "year",
                "Km": "kilometers",
                "Combustibil": "fuelType",
                "Putere": "horsePower",
                "Transmisie": "transmission",
                "Culoare": "color",
                "Norma de poluare": "emissionStandard",
                "Tip Caroserie": "bodyType",
                "Capacitate cilindrica": "engineSize",
                "Cutie de viteze": "gearbox",
            }
            new_data = {}
            for key, value in data.items():
                if key in mapping:
                    new_key = mapping[key]
                    new_data[new_key] = value
            # i have a folder with photos of every car make in car_makes list, if the car make of the new data is in the car makes list, i will create another column called 'photos' which is an array of photos and i will insert the link to the specific photo in the photos pholder
            if new_data['make'] in car_makes:
                new_data['photos'] = [f'{new_data["make"]}.jpg']
            if new_data['price'] is not None:
                collection.insert_one(new_data)

        except Exception as e:
            print(f"Failed to process link: {link}. Error: {str(e)}")
            continue

    client.close()

except Exception as e:
    raise Exception("The following error occurred: ", e)
